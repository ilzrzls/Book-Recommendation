"""
协同过滤 + 内容推荐引擎
当用户评分数据不足时，降级为基于内容的相似度（标签 + 作者）。
"""

import numpy as np
import pymysql
from collections import defaultdict
from sklearn.metrics.pairwise import cosine_similarity
from .config import get_mysql_cfg


class ItemCFRecommender:
    """混合推荐：优先 CF，用户不足则用内容相似度"""

    def __init__(self):
        cfg = get_mysql_cfg()
        self.conn = pymysql.connect(**cfg, autocommit=True)

        self.book_ids = {}      # book_id -> matrix index
        self.rev_book = {}      # matrix index -> (book_id, douban_id, title)
        self.feature_matrix = None  # 内容特征矩阵
        self.sim_matrix = None
        self.mode = 'content'   # 'cf' or 'content'

        self._build_content_features()

    def _build_content_features(self):
        """构建基于内容的特征矩阵（标签 One-Hot + 归一化评分）"""
        cur = self.conn.cursor()

        # 获取所有图书
        cur.execute("SELECT book_id, douban_id, title, score FROM book")
        books = cur.fetchall()

        # 获取所有标签
        cur.execute("SELECT tag_id, name FROM tag")
        all_tags = {r[0]: r[1] for r in cur.fetchall()}
        tag_ids = {tid: i for i, tid in enumerate(all_tags.keys())}

        # 获取图书-标签关系
        cur.execute("SELECT book_id, tag_id FROM book_tag")
        book_tags = defaultdict(set)
        for bid, tid in cur.fetchall():
            book_tags[bid].add(tid)

        # 获取图书-作者关系
        cur.execute("SELECT book_id, author_id FROM book_author")
        book_authors = defaultdict(set)
        for bid, aid in cur.fetchall():
            book_authors[bid].add(aid)
        # 获取所有作者
        cur.execute("SELECT author_id FROM author")
        all_authors = [r[0] for r in cur.fetchall()]
        author_ids = {aid: i for i, aid in enumerate(all_authors)}

        # 获取出版社
        cur.execute("SELECT book_id, publisher_id FROM book WHERE publisher_id IS NOT NULL")
        book_pubs = {r[0]: r[1] for r in cur.fetchall()}

        cur.close()

        n_books = len(books)
        n_tags = len(all_tags)
        n_authors = len(all_authors)
        n_features = n_tags + n_authors + 3  # tags + authors + score + publisher_hot + rating_count

        self.feature_matrix = np.zeros((n_books, n_features))

        for i, (bid, douban_id, title, score) in enumerate(books):
            self.book_ids[bid] = i
            self.rev_book[i] = (bid, douban_id, title)

            # Tag features
            for tid in book_tags.get(bid, set()):
                if tid in tag_ids:
                    self.feature_matrix[i, tag_ids[tid]] = 1.0

            # Author features
            for aid in book_authors.get(bid, set()):
                if aid in author_ids:
                    self.feature_matrix[i, n_tags + author_ids[aid]] = 1.0

            # Score feature (normalized)
            if score:
                self.feature_matrix[i, -3] = float(score) / 10.0

            # Publisher hotness (unique publisher count)
            if bid in book_pubs:
                self.feature_matrix[i, -2] = 1.0

            # Rating count proxy
            self.feature_matrix[i, -1] = 1.0

        print(f"  Content features: {n_books} books × {n_features} features "
              f"({n_tags} tags + {n_authors} authors)")

    def compute_similarity(self):
        """计算内容特征余弦相似度"""
        if self.feature_matrix is None:
            self._build_content_features()
        self.sim_matrix = cosine_similarity(self.feature_matrix)
        np.fill_diagonal(self.sim_matrix, 0)
        self.mode = 'content'
        n = self.sim_matrix.shape[0]
        nnz = np.count_nonzero(self.sim_matrix)
        print(f"  Similarity matrix: {n}×{n} computed, {nnz} non-zero.")

    def similar_books(self, book_id, top_n=10):
        """找到与指定图书最相似的书"""
        if self.sim_matrix is None:
            self.compute_similarity()

        if book_id not in self.book_ids:
            return []

        idx = self.book_ids[book_id]
        sims = self.sim_matrix[idx]
        top_indices = np.argsort(-sims)[:top_n + 1]

        results = []
        for i in top_indices:
            if i == idx:
                continue
            if sims[i] <= 0.01:
                continue
            bid, douban_id, title = self.rev_book[i]
            results.append((douban_id or str(bid), title, float(sims[i]),
                           '内容相似'))
            if len(results) >= top_n:
                break
        return results

    def close(self):
        self.conn.close()


if __name__ == '__main__':
    cf = ItemCFRecommender()
    cf.compute_similarity()

    cur = cf.conn.cursor()
    cur.execute("SELECT book_id FROM book WHERE title='活着' LIMIT 1")
    bid = cur.fetchone()[0]
    cur.close()

    print(f"\n=== 与「活着」最相似的书 ===\n")
    for douban_id, title, sim, reason in cf.similar_books(bid, 10):
        print(f"  [{sim:.3f}] {reason}  →  {title}")
    cf.close()
