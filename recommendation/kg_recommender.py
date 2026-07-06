"""
知识图谱推荐引擎
基于 Neo4j 图路径推理，找出与目标图书关联的候选图书。

路径权重（设计文档 8.2 节）：
  作者路径 WRITTEN_BY     : 0.35
  标签路径 HAS_TAG        : 0.30
  出版社路径 PUBLISHED_BY : 0.20
  系列路径 BELONGS_TO_SERIES : 0.15
"""

from neo4j import GraphDatabase
from .config import get_neo4j_cfg

PATH_WEIGHTS = {
    'WRITTEN_BY': 0.35,
    'HAS_TAG': 0.30,
    'PUBLISHED_BY': 0.20,
    'BELONGS_TO_SERIES': 0.15,
}


class KGRecommender:
    """基于知识图谱的图书推荐"""

    def __init__(self):
        cfg = get_neo4j_cfg()
        self.driver = GraphDatabase.driver(cfg['uri'], auth=(cfg['user'], cfg['password']))
        self.db = cfg.get('database', 'neo4j')

    def recommend_by_book(self, douban_id, top_n=10):
        """
        根据一本书，通过图谱路径找相似书。
        :param douban_id: 豆瓣书籍ID
        :param top_n: 返回数量
        :return: [(douban_id, score, reason), ...]
        """
        cypher = """
        MATCH (source:Book {book_id: $bid})
        // 路径1: 同作者
        OPTIONAL MATCH (source)-[:WRITTEN_BY]->(a:Author)<-[:WRITTEN_BY]-(cand1:Book)
        WHERE cand1 <> source
        WITH source, cand1, 0.35 AS w, '同作者' AS reason
        // 路径2: 同标签
        OPTIONAL MATCH (source)-[:HAS_TAG]->(t:Tag)<-[:HAS_TAG]-(cand2:Book)
        WHERE cand2 <> source AND NOT (source)-[:WRITTEN_BY]->()<-[:WRITTEN_BY]-(cand2)
        WITH source, cand1, w, reason, cand2
        // 路径3: 同出版社
        OPTIONAL MATCH (source)-[:PUBLISHED_BY]->(p:Publisher)<-[:PUBLISHED_BY]-(cand3:Book)
        WHERE cand3 <> source
        WITH collect(DISTINCT {cand: cand1, w: 0.35, reason: '同作者: ' + a.name}) +
                 collect(DISTINCT {cand: cand2, w: 0.30, reason: '同标签: ' + t.name}) +
                 collect(DISTINCT {cand: cand3, w: 0.20, reason: '同出版社: ' + p.name}) AS pool
        UNWIND pool AS entry
        WITH entry.cand AS cand, entry.w AS weight, entry.reason AS reason
        WHERE cand IS NOT NULL
        RETURN cand.book_id AS douban_id, cand.title AS title,
               cand.score AS score, weight, reason,
               COUNT(*) AS path_count
        ORDER BY weight * path_count DESC, cand.score DESC
        LIMIT $n
        """
        with self.driver.session(database=self.db) as session:
            result = session.run(cypher, bid=str(douban_id), n=top_n)
            return [
                (r['douban_id'], r['title'], r['score'],
                 round(r['weight'] * r['path_count'], 2), r['reason'])
                for r in result
            ]

    def recommend_by_book_simple(self, douban_id, top_n=10):
        """简化版：分三条路径查询，Python 合并"""
        scored = {}  # douban_id -> {title, score, weight, reason}

        def _add_books(result, weight, reason_prefix, attr='name'):
            for r in result:
                did = r['douban_id']
                if did == douban_id or did is None:
                    continue
                extra = r.get(attr, '').lstrip(':').strip()
                reason = f'{reason_prefix}: {extra}' if extra else reason_prefix
                if did not in scored:
                    scored[did] = {'douban_id': did, 'title': r['title'],
                                   'score': r['score'] or 0,
                                   'weight': 0, 'reason': reason}
                scored[did]['weight'] += weight

        with self.driver.session(database=self.db) as session:
            # 同作者
            author_recs = session.run("""
                MATCH (source:Book {book_id: $bid})-[:WRITTEN_BY]->(a:Author)<-[:WRITTEN_BY]-(b:Book)
                WHERE b <> source
                RETURN DISTINCT b.book_id AS douban_id, b.title AS title,
                       b.score AS score, a.name AS name
                LIMIT $n
            """, bid=str(douban_id), n=top_n * 2)
            _add_books(author_recs, 0.35, '同作者')

            # 同标签
            tag_recs = session.run("""
                MATCH (source:Book {book_id: $bid})-[:HAS_TAG]->(t:Tag)<-[:HAS_TAG]-(b:Book)
                WHERE b <> source
                RETURN DISTINCT b.book_id AS douban_id, b.title AS title,
                       b.score AS score, t.name AS name
                LIMIT $n
            """, bid=str(douban_id), n=top_n * 2)
            _add_books(tag_recs, 0.30, '同标签')

            # 同出版社
            pub_recs = session.run("""
                MATCH (source:Book {book_id: $bid})-[:PUBLISHED_BY]->(p:Publisher)<-[:PUBLISHED_BY]-(b:Book)
                WHERE b <> source
                RETURN DISTINCT b.book_id AS douban_id, b.title AS title,
                       b.score AS score, p.name AS name
                LIMIT $n
            """, bid=str(douban_id), n=top_n * 2)
            _add_books(pub_recs, 0.20, '同出版社')

        sorted_items = sorted(scored.values(),
                            key=lambda x: x['weight'] * (float(x['score'] or 0) / 10),
                            reverse=True)
        return [(r['douban_id'], r['title'], r['score'],
                 round(r['weight'], 2), r['reason'])
                for r in sorted_items[:top_n]]

    def recommend_by_preferences(self, liked_author=None, liked_tags=None, top_n=10):
        """根据用户偏好（喜欢的作者、标签）推荐"""
        if not liked_author and not liked_tags:
            return self._hot_books(top_n)

        cypher_parts = []
        if liked_author:
            cypher_parts.append("""
            MATCH (a:Author {name: $author})<-[:WRITTEN_BY]-(b:Book)
            RETURN b, 0.35 AS w, '你喜欢作者: ' + a.name AS reason
            """)
        if liked_tags:
            for tag in (liked_tags or []):
                cypher_parts.append(f"""
                MATCH (t:Tag {{name: '{tag}'}})<-[:HAS_TAG]-(b:Book)
                RETURN b, 0.30 AS w, '你喜欢标签: {tag}' AS reason
                """)

        # 简化：合并查询
        cypher = """
        MATCH (b:Book)
        WHERE """
        conditions = []
        if liked_author:
            conditions.append("EXISTS { MATCH (b)-[:WRITTEN_BY]->(:Author {name: $author}) }")
        if liked_tags:
            for tag in liked_tags:
                conditions.append(f"EXISTS {{ MATCH (b)-[:HAS_TAG]->(:Tag {{name: '{tag}'}}) }}")
        cypher += ' OR '.join(conditions)
        cypher += """
        RETURN DISTINCT b.book_id AS douban_id, b.title AS title,
               b.score AS score
        ORDER BY b.score DESC
        LIMIT $n
        """
        with self.driver.session(database=self.db) as session:
            result = session.run(cypher, author=liked_author, n=top_n)
            return [(r['douban_id'], r['title'], r['score'], 0.35, '偏好匹配') for r in result]

    def _hot_books(self, top_n=10):
        """热门图书（按评分降序）"""
        cypher = """
        MATCH (b:Book)
        RETURN b.book_id AS douban_id, b.title AS title,
               b.score AS score
        ORDER BY b.score DESC
        LIMIT $n
        """
        with self.driver.session(database=self.db) as session:
            result = session.run(cypher, n=top_n)
            return [(r['douban_id'], r['title'], r['score'], 0.1, '热门推荐') for r in result]

    def close(self):
        self.driver.close()


if __name__ == '__main__':
    kg = KGRecommender()
    print("=== 从「三体全集」出发的 KG 推荐 ===\n")
    recs = kg.recommend_by_book_simple('6518605', 10)
    for bid, title, score, w, reason in recs:
        print(f"  [{w:.2f}] {reason}  →  {title}  (★{score})")
    kg.close()
