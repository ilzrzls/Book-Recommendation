"""
协同过滤推荐引擎 (Collaborative Filtering)
============================================
核心数据源:
  1. rating         — 显式评分 (1-5星)，权重最高
  2. bookshelf_item — 用户书架（收藏），强隐式信号
  3. reading_progress — 阅读进度，中等隐式信号
  4. user_behavior  — 浏览/点击/评论等隐式行为
  5. comment        — 评论（写评论=深度兴趣）

算法:
  - 构建 user-item 交互矩阵，每种行为类型分配不同权重
  - 基于调整余弦相似度计算 item-item 相似度
  - 基于用户交互历史加权聚合推荐
  - 支持新用户冷启动（降级为热门 + 内容推荐）
"""

import numpy as np
import pymysql
from collections import defaultdict
from scipy.sparse import csr_matrix, lil_matrix
from sklearn.metrics.pairwise import cosine_similarity
from .config import get_mysql_cfg


class CFRecommender:
    """协同过滤推荐引擎 — 隐式反馈 + 显式评分混合"""

    # 行为权重（rating 在外部单独处理，因为它是 1-5 分）
    BEHAVIOR_WEIGHTS = {
        'rating':  5.0,    # 显式评分 (1-5分原值)
        'collect': 4.0,    # 书架收藏
        'read':    3.0,    # 阅读过（reading_progress）
        'comment': 3.5,    # 写了评论
        'rate':    3.0,    # 评分行为（不含分值，额外 signal）
        'share':   2.5,    # 分享
        'click':   1.5,    # 点击
        'view':    1.0,    # 浏览
        'search':  1.0,    # 搜索
        'interested': 4.5, # 显式点赞
    }

    def __init__(self):
        cfg = get_mysql_cfg()
        self.conn = pymysql.connect(**cfg, autocommit=True)

        self.user_ids = {}     # user_id -> matrix row
        self.book_ids = {}     # book_id -> matrix col
        self.rev_user = {}     # matrix row -> user_id
        self.rev_book = {}     # matrix col -> (book_id, douban_id, title)
        self.interaction_matrix = None  # sparse user-item
        self.item_sim = None           # item-item similarity
        self.book_tags = {}            # book_id -> set(tag_names) 用于内容质检

        self._load_data()
        self._load_tags()

    # ═══════════════════════ 数据加载 ═══════════════════════

    def _load_data(self):
        """从多张表加载用户-物品交互，构建加权矩阵"""
        cur = self.conn.cursor()

        # 获取所有活跃图书（status=1）
        cur.execute("SELECT book_id, douban_id, title FROM book WHERE status=1")
        books = cur.fetchall()
        for i, (bid, douban_id, title) in enumerate(books):
            self.book_ids[bid] = i
            self.rev_book[i] = (bid, douban_id, title)
        print(f"  [CF] 图书: {len(books)} 本")

        # 获取有行为的用户
        user_set = set()

        # 1. rating 表
        cur.execute("SELECT user_id FROM rating")
        user_set.update(r[0] for r in cur.fetchall())

        # 2. user_behavior 表
        cur.execute("SELECT DISTINCT user_id FROM user_behavior")
        user_set.update(r[0] for r in cur.fetchall())

        # 3. bookshelf_item 表 (通过 bookshelf 获取 user_id)
        cur.execute("SELECT DISTINCT s.user_id FROM bookshelf_item i JOIN bookshelf s ON i.shelf_id=s.shelf_id")
        user_set.update(r[0] for r in cur.fetchall())

        # 4. reading_progress 表
        cur.execute("SELECT DISTINCT user_id FROM reading_progress")
        user_set.update(r[0] for r in cur.fetchall())

        # 5. comment 表
        cur.execute("SELECT DISTINCT user_id FROM comment")
        user_set.update(r[0] for r in cur.fetchall())

        cur.close()

        users = sorted(user_set)
        for i, uid in enumerate(users):
            self.user_ids[uid] = i
            self.rev_user[i] = uid
        print(f"  [CF] 活跃用户: {len(users)} 人")

        n_users = len(users)
        n_books = len(books)
        # 使用 scipy sparse 构建交互矩阵 (初始化为 LIL 方便赋值)
        self.interaction_matrix = lil_matrix((n_users, n_books), dtype=np.float32)

        # ── 填充数据 ──
        cur = self.conn.cursor()

        # 1. 评分 (rating) — 1~5 分直接使用
        cur.execute("SELECT user_id, book_id, score FROM rating")
        for uid, bid, score in cur.fetchall():
            if uid in self.user_ids and bid in self.book_ids:
                self.interaction_matrix[self.user_ids[uid], self.book_ids[bid]] += score

        # 2. 书架收藏 (bookshelf_item → bookshelf)
        cur.execute("""
            SELECT s.user_id, i.book_id
            FROM bookshelf_item i
            JOIN bookshelf s ON i.shelf_id = s.shelf_id
        """)
        for uid, bid in cur.fetchall():
            if uid in self.user_ids and bid in self.book_ids:
                self.interaction_matrix[self.user_ids[uid], self.book_ids[bid]] += self.BEHAVIOR_WEIGHTS['collect']

        # 3. 阅读进度 (reading_progress) — 进度>10% 才算读了
        cur.execute("SELECT user_id, book_id FROM reading_progress WHERE progress_pct >= 10")
        for uid, bid in cur.fetchall():
            if uid in self.user_ids and bid in self.book_ids:
                self.interaction_matrix[self.user_ids[uid], self.book_ids[bid]] += self.BEHAVIOR_WEIGHTS['read']

        # 4. 评论 (comment) — 写了评论=深度参与
        cur.execute("SELECT user_id, book_id FROM comment")
        for uid, bid in cur.fetchall():
            if uid in self.user_ids and bid in self.book_ids:
                self.interaction_matrix[self.user_ids[uid], self.book_ids[bid]] += self.BEHAVIOR_WEIGHTS['comment']

        # 5. 其他行为 (user_behavior)
        cur.execute("SELECT user_id, action_type, target_id FROM user_behavior WHERE target_type='book'")
        for uid, atype, bid in cur.fetchall():
            if uid in self.user_ids and bid in self.book_ids:
                w = self.BEHAVIOR_WEIGHTS.get(atype, 1.0)
                self.interaction_matrix[self.user_ids[uid], self.book_ids[bid]] += w

        cur.close()

        # 转换为 CSR 格式以提高运算效率
        self.interaction_matrix = self.interaction_matrix.tocsr()
        nnz = self.interaction_matrix.nnz
        density = 100.0 * nnz / (n_users * n_books) if n_users * n_books > 0 else 0
        print(f"  [CF] 交互矩阵: {n_users}×{n_books}, {nnz} 非零 ({density:.2f}% 稠密)")

    def _load_tags(self):
        """加载每本书的标签集合，用于 CF 推荐的内容相关性质检"""
        cur = self.conn.cursor()
        cur.execute("SELECT book_id, tag_id FROM book_tag")
        book_tag_ids = {}
        for bid, tid in cur.fetchall():
            book_tag_ids.setdefault(bid, set()).add(tid)
        # 获取tag_id -> name映射
        cur.execute("SELECT tag_id, name FROM tag")
        tag_names = {r[0]: r[1] for r in cur.fetchall()}
        for bid in self.book_ids:
            tids = book_tag_ids.get(bid, set())
            self.book_tags[bid] = {tag_names[tid] for tid in tids if tid in tag_names}
        tagged = sum(1 for tags in self.book_tags.values() if tags)
        print(f"  [CF] 标签索引: {tagged} 本书有标签数据")
        cur.close()

    # ═══════════════════════ 相似度计算 ═══════════════════════

    def compute_similarity(self):
        """基于调整余弦相似度计算 Item-Item 相似度矩阵。
        调整项：减去用户均值，消除用户评分偏置。
        共现过滤：至少 2 个用户共同交互过的物品才计算相似度。
        """
        M = self.interaction_matrix  # CSR, (n_users, n_books)
        n_users, n_books = M.shape

        if n_users == 0 or n_books == 0:
            print("  [CF] 无足够数据计算相似度")
            self.item_sim = np.eye(n_books)
            return

        # 转为稠密矩阵（250本书规模完全没问题）
        dense = M.toarray().astype(np.float64)

        # 调整余弦相似度：减去每个用户的均值（排除零）
        row_counts = np.diff(M.indptr)
        row_sums = np.asarray(M.sum(axis=1)).flatten()
        row_means = np.divide(row_sums, row_counts, where=row_counts > 0, out=np.zeros_like(row_sums))
        row_means = row_means.reshape(-1, 1)

        adjusted = np.where(dense > 0, dense - row_means, 0)

        # 计算共现矩阵：每对物品被多少用户共同交互
        binary = (dense > 0).astype(np.int32)
        cooccur = binary.T @ binary  # (n_books, n_books) 共现次数

        # Item-Item 余弦相似度
        item_vectors = adjusted.T
        raw_sim = cosine_similarity(item_vectors)
        np.fill_diagonal(raw_sim, 0)

        # 共现过滤：至少 MIN_COOCCUR 个用户共现才保留相似度
        MIN_COOCCUR = 2
        self.item_sim = np.where(cooccur >= MIN_COOCCUR, raw_sim, 0)

        above_threshold = np.count_nonzero(cooccur >= MIN_COOCCUR) - n_books  # 排除对角线
        nnz_sim = np.count_nonzero(self.item_sim)
        print(f"  [CF] Item-Item 相似度: {n_books}x{n_books}, "
              f"共现>={MIN_COOCCUR}: {above_threshold} 对, "
              f"有效相似度: {nnz_sim} ({100*nnz_sim/(n_books*n_books):.1f}%)")

    # ═══════════════════════ 推荐 ═══════════════════════

    def recommend_for_user(self, user_id, top_n=20, exclude_ids=None):
        """为指定用户生成多样化个性化推荐。
        策略：从用户交互过的多本书中分别取 Top-3 相似书，
        限制每本来源书最多贡献 3 条，确保多样性。
        """
        exclude_ids = exclude_ids or []
        if user_id not in self.user_ids:
            return self._cold_start(top_n, exclude_ids)

        if self.item_sim is None:
            self.compute_similarity()

        user_idx = self.user_ids[user_id]
        user_row = self.interaction_matrix[user_idx]
        interacted = user_row.indices
        weights = user_row.data

        if len(interacted) == 0:
            return self._cold_start(top_n, exclude_ids)

        # 按权重降序排列用户交互过的书
        sorted_pairs = sorted(zip(interacted, weights), key=lambda x: -x[1])

        # 排除集合
        exclude_set = set(interacted.tolist())
        for bid in exclude_ids:
            if bid in self.book_ids:
                exclude_set.add(self.book_ids[bid])

        MAX_PER_SOURCE = max(2, top_n // max(1, len(sorted_pairs)))
        seen_indices = set()
        results = []

        for i_idx, w in sorted_pairs:
            if i_idx >= self.item_sim.shape[0]:
                continue
            src_bid = self.rev_book[i_idx][0] if i_idx in self.rev_book else None
            src_tags = self.book_tags.get(src_bid, set())
            sim_row = np.maximum(self.item_sim[i_idx], 0)
            top_local = np.argsort(-sim_row)
            count_from_this = 0
            for j in top_local:
                if j == i_idx or j in exclude_set or j in seen_indices:
                    continue
                if sim_row[j] <= 0.01:
                    continue
                if count_from_this >= MAX_PER_SOURCE:
                    break

                # ── 内容相关性质检：源书和推荐书至少共享1个标签 ──
                tgt_bid = self.rev_book[j][0] if j in self.rev_book else None
                tgt_tags = self.book_tags.get(tgt_bid, set())
                if src_tags and tgt_tags:
                    common = src_tags & tgt_tags
                    # 排除泛化标签"外国文学""小说""文学"（太宽泛无意义）
                    meaningful = common - {'外国文学', '小说', '文学', '经典名著', '历史'}
                    if not meaningful:
                        continue  # 跳过无意义关联

                bid, douban_id, title = self.rev_book[j]
                _, _, src_title = self.rev_book[i_idx] if i_idx in self.rev_book else ('', '', '?')
                results.append({
                    'douban_id': douban_id or str(bid),
                    'title': title,
                    'book_id': bid,
                    'score': round(float(w * (sim_row[j] ** 1.5)), 3),
                    'reason': f'因为你读过《{src_title}》',
                })
                seen_indices.add(j)
                count_from_this += 1
            if len(results) >= top_n:
                break

        # 如果来源书太少，用热门补足
        if len(results) < top_n:
            hot = self._hot_books(top_n - len(results),
                                  exclude_set | seen_indices | set(r['book_id'] for r in results))
            results.extend(hot)

        return results[:top_n]

    def similar_items(self, book_id, top_n=10):
        """给定一本书，返回CF相似的书"""
        if book_id not in self.book_ids:
            return []
        if self.item_sim is None:
            self.compute_similarity()

        idx = self.book_ids[book_id]
        sims = self.item_sim[idx]
        top_indices = np.argsort(-sims)[:top_n + 1]

        results = []
        for i in top_indices:
            if i == idx or sims[i] <= 0.01:
                continue
            bid, douban_id, title = self.rev_book[i]
            results.append({
                'douban_id': douban_id or str(bid),
                'title': title,
                'book_id': bid,
                'score': round(float(sims[i]), 3),
                'reason': '读者也喜欢',
            })
            if len(results) >= top_n:
                break
        return results

    # ═══════════════════════ 辅助方法 ═══════════════════════

    def _gen_reason(self, user_idx, rec_idx, interacted, weights):
        """生成推荐理由：找出对该推荐贡献最大的已读图书"""
        sims = self.item_sim[rec_idx]
        best_i_local = None
        best_score = -1
        for i_idx, w in zip(interacted, weights):
            s = w * (max(sims[i_idx], 0) ** 1.5)
            if s > best_score and i_idx < len(self.rev_book):
                best_score = s
                best_i_local = i_idx

        if best_i_local is not None:
            _, _, title = self.rev_book[best_i_local]
            return f'因为你读过《{title}》'
        n_ints = len(interacted)
        return f'基于你的{n_ints}本阅读记录'

    def _cold_start(self, top_n, exclude_set=None):
        """冷启动：无用户数据时返回热门 + 高分书"""
        return self._hot_books(top_n, exclude_set or set())

    def _hot_books(self, top_n, exclude_set):
        """高分+多评论的热门书"""
        cur = self.conn.cursor()
        cur.execute("""
            SELECT b.book_id, b.douban_id, b.title, b.score, b.votes
            FROM book b WHERE b.status=1
            ORDER BY b.score DESC, b.votes DESC LIMIT %s
        """, (top_n + len(exclude_set),))
        rows = cur.fetchall()
        cur.close()
        results = []
        for r in rows:
            if r[0] in exclude_set:
                continue
            results.append({
                'douban_id': r[1] or str(r[0]), 'title': r[2],
                'book_id': r[0],
                'score': round(float(r[3]) / 10 if r[3] else 0.5, 3),
                'reason': '热门推荐',
            })
            if len(results) >= top_n:
                break
        return results

    def update_user_interaction(self, user_id, book_id, action_type, value=1.0):
        """增量更新：用户做了新行为时调用，实时更新矩阵（不需要重建）"""
        if user_id not in self.user_ids or book_id not in self.book_ids:
            return
        w = self.BEHAVIOR_WEIGHTS.get(action_type, value)
        self.interaction_matrix[self.user_ids[user_id], self.book_ids[book_id]] += w
        # 标记相似度需重新计算
        self.item_sim = None

    def close(self):
        self.conn.close()


# ═══════════════════════ 测试 ═══════════════════════
if __name__ == '__main__':
    cf = CFRecommender()
    cf.compute_similarity()

    # 测试1: 找个用户做个性化推荐
    cur = cf.conn.cursor()
    cur.execute("SELECT user_id, username FROM user LIMIT 1")
    test_user = cur.fetchone()
    cur.close()

    if test_user:
        uid, uname = test_user
        print(f"\n=== 为「{uname}」(id={uid}) 个性化推荐 ===")
        recs = cf.recommend_for_user(uid, 10)
        for i, r in enumerate(recs):
            print(f"  {i+1}. [{r['score']:.3f}] {r['title']} — {r['reason']}")
    else:
        print("\n无用户数据，冷启动推荐:")
        recs = cf.recommend_for_user(99999, 10)
        for i, r in enumerate(recs):
            print(f"  {i+1}. [{r['score']:.3f}] {r['title']} — {r['reason']}")

    # 测试2: 相似物品
    cur = cf.conn.cursor()
    cur.execute("SELECT book_id, title FROM book WHERE title LIKE '%活着%' LIMIT 1")
    row = cur.fetchone()
    cur.close()
    if row:
        print(f"\n=== CF: 与「{row[1]}」相似的书 ===")
        for r in cf.similar_items(row[0], 8):
            print(f"  [{r['score']:.3f}] {r['title']} — {r['reason']}")

    cf.close()
