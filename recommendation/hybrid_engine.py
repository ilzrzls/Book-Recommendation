"""
混合推荐引擎 v2
融合五种策略：
  知识图谱推荐 (KG)    : 权重 0.30  (可解释性强，路径加权)
  协同过滤推荐 (CF)    : 权重 0.30  (用户行为驱动，精准)
  内容相似推荐 (Content): 权重 0.25  (标签/作者/描述文本)
  热门推荐 (Hot)       : 权重 0.10  (冷启动保底)
  新书推荐 (New)       : 权重 0.05  (时效性)

同时提供推荐理由生成。
"""

import pymysql
from .kg_recommender import KGRecommender
from .content_recommender import ContentRecommender
from .cf_recommender import CFRecommender
from .config import get_mysql_cfg


class HybridRecommender:
    """混合推荐引擎 v2"""

    def __init__(self):
        self.kg = None
        self.kg_available = False
        try:
            self.kg = KGRecommender()
            self.kg_available = True
            print("  KG recommender: ready")
        except Exception as e:
            print(f"  KG recommender unavailable: {e}")

        self.content = ContentRecommender()
        self.cf = CFRecommender()
        print("  CF recommender: ready")
        cfg = get_mysql_cfg()
        self.conn = pymysql.connect(**cfg, autocommit=True)

        # 权重配置
        if self.kg_available:
            self.weights = {'kg': 0.30, 'cf': 0.30, 'content': 0.25, 'hot': 0.10, 'new': 0.05}
        else:
            self.weights = {'kg': 0.00, 'cf': 0.40, 'content': 0.35, 'hot': 0.15, 'new': 0.10}

    # ── 按书推荐（图书详情页"相似图书"）──

    def similar_books(self, book_id, top_n=10):
        """给定一本书，返回相似推荐"""
        cur = self.conn.cursor()
        cur.execute("SELECT douban_id FROM book WHERE book_id=%s", (book_id,))
        row = cur.fetchone()
        cur.close()
        douban_id = str(row[0]) if row and row[0] else None

        kg_recs = []
        if self.kg_available and douban_id:
            try:
                kg_recs = self.kg.recommend_by_book_simple(douban_id, top_n * 2)
            except Exception as e:
                print(f"  KG rec error: {e}")

        content_recs = self.content.similar_books(book_id, top_n * 2)

        return self._merge(kg_recs, content_recs, top_n)

    # ── 首页推荐（基于用户偏好）──

    def homepage_recommend(self, user_id=None, top_n=20, exclude_ids=None):
        """首页个性化推荐。有 user_id 时用 CF + KG + Content 混合；
           无 user_id 时（游客）用高分种子 + KG + Content。"""
        exclude_ids = exclude_ids or []

        scored = {}  # douban_id -> {title, score, reasons}

        # ── 1. 协同过滤（用户行为驱动）──
        if user_id:
            cf_recs = self.cf.recommend_for_user(user_id, top_n=top_n, exclude_ids=exclude_ids)
            for r in cf_recs:
                did = str(r['douban_id'])
                scored[did] = {'title': r['title'], 'score': 0, 'reasons': [r['reason']],
                               'book_id': r.get('book_id')}
                scored[did]['score'] += self.weights['cf'] * r['score']

        # ── 2. 知识图谱 ──
        if self.kg_available and user_id:
            # 取用户交互过的书的 douban_id 作为 KG 种子
            cur = self.conn.cursor()
            cur.execute("""
                SELECT b.douban_id, MAX(r.score) as ms
                FROM rating r JOIN book b ON r.book_id=b.book_id WHERE r.user_id=%s
                GROUP BY b.douban_id ORDER BY ms DESC LIMIT 5
            """, (user_id,))
            kg_seeds = [r[0] for r in cur.fetchall()]
            cur.close()
            for did in kg_seeds:
                if did:
                    kg_recs = self.kg.recommend_by_book_simple(str(did), 8)
                    for item in kg_recs:
                        did2, title, raw_score, w, reason = item
                        did2 = str(did2)
                        if did2 not in scored:
                            scored[did2] = {'title': title, 'score': 0, 'reasons': []}
                        scored[did2]['score'] += w * self.weights['kg']
                        if reason not in scored[did2]['reasons']:
                            scored[did2]['reasons'].append(reason)

        # ── 3. 内容推荐（用户自己的书做种子，而非全局高分）──
        cur = self.conn.cursor()
        if user_id:
            # 用户评分/收藏过的书 → 内容相似推荐
            cur.execute("""
                SELECT b.book_id, MAX(COALESCE(r.score, 0)) AS ms FROM book b
                LEFT JOIN rating r ON b.book_id=r.book_id AND r.user_id=%s
                LEFT JOIN bookshelf_item bsi ON b.book_id=bsi.book_id
                LEFT JOIN bookshelf bs ON bsi.shelf_id=bs.shelf_id AND bs.user_id=%s
                WHERE (r.user_id IS NOT NULL OR bs.user_id IS NOT NULL)
                AND b.description NOT LIKE '用户创作%%'
                GROUP BY b.book_id ORDER BY ms DESC LIMIT 8
            """, (user_id, user_id))
        else:
            cur.execute("SELECT book_id FROM book WHERE score IS NOT NULL AND description NOT LIKE '用户创作%%' ORDER BY score DESC LIMIT 5")
        content_seeds = [r[0] for r in cur.fetchall()]
        cur.close()

        for bid in content_seeds:
            cr = self.content.similar_books(bid, top_n=8)
            for r in cr:
                did = str(r['douban_id'])
                if did not in scored:
                    scored[did] = {'title': r['title'], 'score': 0, 'reasons': [], 'book_id': r.get('book_id')}
                scored[did]['score'] += r['score'] * self.weights['content']
                if r['reason'] and r['reason'] not in scored[did]['reasons']:
                    scored[did]['reasons'].append(r['reason'])

        # ── 4. 多样化补充：热门 + 冷门 + 入门 + 新书 ──
        # 每种策略取少量，混合后不会让单一策略垄断
        supplements = []
        supplements.extend(self.hot_books(max(1, top_n // 2)))
        supplements.extend(self.hidden_gems(max(1, top_n // 4)))
        if not user_id:  # 未登录多推入门书
            supplements.extend(self.beginner_books(max(1, top_n // 3)))
        supplements.extend(self.new_books(max(1, top_n // 5)))
        for item in supplements:
            did, title, raw_score, w, reason = item
            did = str(did)
            if did not in scored:
                scored[did] = {'title': title, 'score': 0, 'reasons': [reason], 'book_id': None}
                scored[did]['score'] += w * self.weights.get('hot', 0.10)

        # ── 5. 合并排序 ──
        sorted_items = sorted(scored.items(), key=lambda x: x[1]['score'], reverse=True)
        results = []
        for did, info in sorted_items[:top_n]:
            results.append({
                'douban_id': did,
                'title': info['title'],
                'book_id': info.get('book_id'),
                'score': round(info['score'], 3),
                'reason': ' / '.join(info['reasons'][:3]),
            })
        return results

    # ── 热门推荐 ──

    def hot_books(self, top_n=10):
        """热门推荐：评分高 + 评价人数多"""
        cur = self.conn.cursor()
        cur.execute("""
            SELECT b.book_id, b.douban_id, b.title, b.score, b.votes
            FROM book b WHERE b.status=1
            ORDER BY b.score DESC, b.votes DESC LIMIT %s
        """, (top_n * 2,))
        rows = cur.fetchall()
        cur.close()
        results = []
        for r in rows:
            score = float(r[3]) if r[3] else 0
            votes = int(r[4]) if r[4] else 0
            if votes > 100000:
                reason = '热门必读 · %d万+ 读者' % (votes // 10000)
            elif votes > 50000:
                reason = '热门推荐 · %d万+ 读者' % (votes // 10000)
            else:
                reason = '热门推荐'
            results.append((r[1] or str(r[0]), r[2], score, 0.10, reason))
        return results

    # ── 冷门佳作 ──

    def hidden_gems(self, top_n=10):
        """冷门佳作：评分高但评价人数少的好书"""
        cur = self.conn.cursor()
        cur.execute("""
            SELECT b.book_id, b.douban_id, b.title, b.score, b.votes
            FROM book b WHERE b.status=1 AND b.score >= 8.5 AND b.votes < 5000
            ORDER BY b.score DESC LIMIT %s
        """, (top_n,))
        rows = cur.fetchall()
        cur.close()
        results = []
        for r in rows:
            score = float(r[3]) if r[3] else 0
            reason = '冷门佳作 · 小众好书'
            results.append((r[1] or str(r[0]), r[2], score, 0.08, reason))
        return results

    # ── 入门推荐 ──

    def beginner_books(self, top_n=10):
        """入门推荐：短小精悍的好书（< 300页且评分高）"""
        cur = self.conn.cursor()
        cur.execute("""
            SELECT b.book_id, b.douban_id, b.title, b.score, b.total_pages
            FROM book b WHERE b.status=1 AND b.total_pages IS NOT NULL
            AND b.total_pages > 0 AND b.total_pages <= 300 AND b.score >= 8.0
            ORDER BY b.score DESC LIMIT %s
        """, (top_n,))
        rows = cur.fetchall()
        cur.close()
        results = []
        for r in rows:
            score = float(r[3]) if r[3] else 0
            pages = int(r[4]) if r[4] else 0
            reason = '入门推荐 · %d页 · 轻松好读' % pages
            results.append((r[1] or str(r[0]), r[2], score, 0.06, reason))
        return results

    # ── 新书推荐 ──

    def new_books(self, top_n=10):
        """新书推荐：最近入库的书"""
        cur = self.conn.cursor()
        cur.execute("""
            SELECT book_id, douban_id, title, score FROM book WHERE status=1
            AND description NOT LIKE '用户创作%%'
            ORDER BY created_at DESC LIMIT %s
        """, (top_n,))
        rows = cur.fetchall()
        cur.close()
        return [(r[1] or str(r[0]), r[2], float(r[3]) if r[3] else 0,
                 0.05, '新书上架') for r in rows]

    # ── 合并策略 ──

    def _merge(self, kg_recs, content_recs, top_n):
        """合并 KG 和 内容推荐结果，KG 理由优先"""
        scored = {}  # douban_id(str) -> (title, total_score, reasons[])

        for item in kg_recs:
            did, title, score, w, reason = item
            did = str(did)  # 统一为字符串
            if did not in scored:
                scored[did] = [title, 0, []]
            scored[did][1] += w * self.weights['kg']
            scored[did][2].append(reason)

        for item in content_recs:
            did = str(item['douban_id'])  # 统一为字符串
            title = item['title']
            sim = item['score']
            reason = item.get('reason', '内容相似')
            if did not in scored:
                scored[did] = [title, 0, []]
            scored[did][1] += sim * self.weights['content']
            # 只有 KG 没给理由时才用内容理由
            if not scored[did][2]:
                scored[did][2].append(reason)

        # 排序
        sorted_items = sorted(scored.items(), key=lambda x: x[1][1], reverse=True)
        results = []
        for did, (title, score, reasons) in sorted_items[:top_n]:
            results.append({
                'douban_id': did,
                'title': title,
                'score': round(score, 3),
                'reason': ' / '.join(reasons[:2]),
            })
        return results

    # ── 单本书完整推荐结果 ──

    def recommend_for_book(self, book_id, top_n=10):
        """为指定图书生成完整推荐"""
        # 混合推荐
        mixed = self.similar_books(book_id, top_n)

        # 补充热门（如果不够）
        if len(mixed) < top_n:
            hot = self.hot_books(top_n - len(mixed))
            for item in hot:
                did, title, score, w, reason = item
                if did not in {r['douban_id'] for r in mixed}:
                    mixed.append({
                        'douban_id': did, 'title': title,
                        'score': w, 'reason': reason,
                    })

        return mixed[:top_n]

    def close(self):
        if self.kg: self.kg.close()
        self.content.close()
        self.cf.close()
        self.conn.close()


if __name__ == '__main__':
    engine = HybridRecommender()

    print("=== 热门推荐 ===\n")
    for item in engine.hot_books(10):
        print(f"  [{item[3]:.2f}] {item[4]}  →  {item[2]}  (★{item[3]*90:.0f})")

    print("\n=== 与「活着」相似的书 ===\n")
    cur = engine.conn.cursor()
    cur.execute("SELECT book_id FROM book WHERE title='活着' LIMIT 1")
    bid = cur.fetchone()[0]
    cur.close()
    for item in engine.recommend_for_book(bid, 10):
        print(f"  [{item['score']:.3f}] {item['title']}")
        print(f"       理由: {item['reason']}")

    engine.close()
