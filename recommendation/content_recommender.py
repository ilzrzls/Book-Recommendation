"""
升级版内容推荐：TF-IDF 文本相似度 + 标签 Jaccard + 作者匹配
多信号融合，比简单标签匹配更准确。
"""
import numpy as np
import pymysql
import jieba
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from collections import defaultdict
from .config import get_mysql_cfg


class ContentRecommender:
    """多信号内容推荐引擎"""

    def __init__(self):
        cfg = get_mysql_cfg()
        self.conn = pymysql.connect(**cfg, autocommit=True)

        self.book_ids = {}       # book_id -> index
        self.rev_book = {}       # index -> (book_id, douban_id, title)
        self.author_sim = None   # 作者 Jaccard 相似度
        self.tag_sim = None      # 标签 Jaccard 相似度
        self.desc_sim = None     # TF-IDF 描述相似度
        self.ensemble_sim = None # 融合相似度

        self._build_all()

    def _build_all(self):
        """构建全部特征矩阵"""
        cur = self.conn.cursor()
        cur.execute("SELECT book_id, douban_id, title, description, score FROM book")
        books = [{'id': r[0], 'douban_id': r[1], 'title': r[2],
                  'desc': r[3] or '', 'score': r[4] or 0} for r in cur.fetchall()]
        cur.close()

        n = len(books)
        for i, b in enumerate(books):
            self.book_ids[b['id']] = i
            self.rev_book[i] = (b['id'], b['douban_id'], b['title'])

        # 加载标签名和作者名（用于生成具体推荐理由）
        self._book_tag_names = {}
        self._book_author_names = {}
        self._book_scores = {}
        self._book_votes = {}
        cur = self.conn.cursor()
        cur.execute("SELECT bt.book_id, t.name FROM book_tag bt JOIN tag t ON bt.tag_id=t.tag_id")
        for bid, tname in cur.fetchall():
            self._book_tag_names.setdefault(bid, set()).add(tname)
        cur.execute("SELECT ba.book_id, a.name FROM book_author ba JOIN author a ON ba.author_id=a.author_id")
        for bid, aname in cur.fetchall():
            self._book_author_names.setdefault(bid, set()).add(aname)
        cur.execute("SELECT book_id, COALESCE(score,0), COALESCE(votes,0) FROM book")
        for bid, sc, vt in cur.fetchall():
            self._book_scores[bid] = float(sc) if sc else 0
            self._book_votes[bid] = int(vt) if vt else 0
        cur.close()

        # 1. TF-IDF 描述相似度（jieba 分词）
        descs = [' '.join(jieba.cut(b['desc'])) for b in books]
        tfidf = TfidfVectorizer(max_features=2000, sublinear_tf=True)
        tfidf_matrix = tfidf.fit_transform(descs)
        self.desc_sim = cosine_similarity(tfidf_matrix)
        np.fill_diagonal(self.desc_sim, 0)

        # 2. 标签 Jaccard 相似度
        book_tags = defaultdict(set)
        cur = self.conn.cursor()
        cur.execute("SELECT book_id, tag_id FROM book_tag")
        for bid, tid in cur.fetchall():
            book_tags[bid].add(tid)
        cur.close()

        self.tag_sim = np.zeros((n, n))
        for i in range(n):
            bi = books[i]['id']
            ti = book_tags.get(bi, set())
            for j in range(i + 1, n):
                bj = books[j]['id']
                tj = book_tags.get(bj, set())
                if not ti or not tj:
                    continue
                jaccard = len(ti & tj) / len(ti | tj)
                self.tag_sim[i, j] = jaccard
                self.tag_sim[j, i] = jaccard

        # 3. 作者 Jaccard 相似度
        book_authors = defaultdict(set)
        cur = self.conn.cursor()
        cur.execute("SELECT book_id, author_id FROM book_author")
        for bid, aid in cur.fetchall():
            book_authors[bid].add(aid)
        cur.close()

        self.author_sim = np.zeros((n, n))
        for i in range(n):
            ai = book_authors.get(books[i]['id'], set())
            for j in range(i + 1, n):
                aj = book_authors.get(books[j]['id'], set())
                if not ai or not aj:
                    continue
                jaccard = len(ai & aj) / len(ai | aj)
                self.author_sim[i, j] = jaccard
                self.author_sim[j, i] = jaccard

        # 4. 融合 (tag 0.4 + desc 0.35 + author 0.25)，标签权重最高因为最可靠
        self.ensemble_sim = (
            0.35 * self.desc_sim +
            0.40 * self.tag_sim +
            0.25 * self.author_sim
        )
        # 归一化每行到 0-1
        row_max = self.ensemble_sim.max(axis=1, keepdims=True)
        row_max[row_max == 0] = 1
        self.ensemble_sim = self.ensemble_sim / row_max

        nnz = np.count_nonzero(self.ensemble_sim)
        print(f"  TF-IDF desc sim: {n}×{n}")
        print(f"  Tag Jaccard: {np.count_nonzero(self.tag_sim)} non-zero")
        print(f"  Author Jaccard: {np.count_nonzero(self.author_sim)} non-zero")
        print(f"  Ensemble: {n}×{n}, {nnz} non-zero")

    def similar_books(self, book_id, top_n=10):
        """融合多信号找最相似的书，返回具体标签/作者名作为理由"""
        if book_id not in self.book_ids:
            return []

        idx = self.book_ids[book_id]
        src_tags = self._book_tag_names.get(book_id, set())
        src_authors = self._book_author_names.get(book_id, set())

        sims = self.ensemble_sim[idx]
        top_indices = np.argsort(-sims)[:top_n + 1]

        # 这些标签太泛化，不作为推荐理由
        BORING_TAGS = {'外国文学','小说','文学','经典名著','经典','历史','中国文学',
                       '外国名著','名著','世界名著','文学名著'}

        results = []
        for i in top_indices:
            if i == idx or sims[i] < 0.1:
                continue
            bid, douban_id, title = self.rev_book[i]
            tgt_tags = self._book_tag_names.get(bid, set())
            tgt_authors = self._book_author_names.get(bid, set())

            # 生成具体理由：标签、作者、评分
            parts = []
            # 标签重叠（过滤泛化标签）
            common_tags = src_tags & tgt_tags - BORING_TAGS
            if common_tags:
                top_tags = list(common_tags)[:2]
                parts.append('同标签: ' + ', '.join(top_tags))
            # 作者重叠
            common_authors = src_authors & tgt_authors
            if common_authors:
                parts.append('同作者: ' + ', '.join(list(common_authors)[:2]))
            # 内容兜底
            if self.desc_sim[idx, i] > 0.1 and not parts:
                parts.append('内容相似')

            results.append({
                'douban_id': douban_id or str(bid),
                'title': title,
                'book_id': bid,
                'score': round(float(sims[i]), 3),
                'reason': ' / '.join(parts) if parts else '内容相似',
            })
            if len(results) >= top_n:
                break
        return results

    def close(self):
        self.conn.close()


if __name__ == '__main__':
    cr = ContentRecommender()
    cur = cr.conn.cursor()

    for test_title in ['银河帝国：基地七部曲', '活着', '三体全集']:
        cur.execute("SELECT book_id FROM book WHERE title=%s LIMIT 1", (test_title,))
        row = cur.fetchone()
        if not row:
            continue
        bid = row[0]
        print(f"\n=== 与「{test_title}」最相似的书 ===")
        recs = cr.similar_books(bid, 8)
        for r in recs:
            d = r['details']
            print(f"  [{r['score']:.3f}] {r['title']}")
            print(f"       reason: {r['reason']}  (desc:{d['desc_sim']:.3f} tag:{d['tag_sim']:.3f} author:{d['author_sim']:.3f})")

    cur.close(); cr.close()
