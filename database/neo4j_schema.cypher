// ============================================================
// 基于知识图谱的个性化荐书系统 - Neo4j 图数据库 Schema
// 数据库: bookgraph
// 版本: 1.0
// 依据: 04-基于知识图谱的个性化荐书系统-概要设计文档
// ============================================================
// 运行方式:
//   方法1: 复制到 Neo4j Browser (http://localhost:7474) 执行
//   方法2: cypher-shell -u neo4j -p bookrec2024 -f neo4j_schema.cypher
// ============================================================

// --- 1. 创建约束 (Constraints) ---
// 约束同时创建了索引，确保实体唯一性

CREATE CONSTRAINT book_id_unique   IF NOT EXISTS FOR (b:Book)      REQUIRE b.book_id IS UNIQUE;
CREATE CONSTRAINT author_id_unique IF NOT EXISTS FOR (a:Author)    REQUIRE a.author_id IS UNIQUE;
CREATE CONSTRAINT publisher_id_unique IF NOT EXISTS FOR (p:Publisher) REQUIRE p.publisher_id IS UNIQUE;
CREATE CONSTRAINT tag_id_unique    IF NOT EXISTS FOR (t:Tag)       REQUIRE t.tag_id IS UNIQUE;
CREATE CONSTRAINT series_id_unique IF NOT EXISTS FOR (s:Series)    REQUIRE s.series_id IS UNIQUE;

// --- 2. 创建索引 (Indexes) ---
// 加速非主键字段的查询

CREATE INDEX book_title_idx     IF NOT EXISTS FOR (b:Book)      ON (b.title);
CREATE INDEX book_score_idx     IF NOT EXISTS FOR (b:Book)      ON (b.score);
CREATE INDEX book_year_idx      IF NOT EXISTS FOR (b:Book)      ON (b.publish_year);
CREATE INDEX author_name_idx    IF NOT EXISTS FOR (a:Author)    ON (a.name);
CREATE INDEX publisher_name_idx IF NOT EXISTS FOR (p:Publisher) ON (p.name);
CREATE INDEX tag_name_idx       IF NOT EXISTS FOR (t:Tag)       ON (t.name);
CREATE INDEX series_name_idx    IF NOT EXISTS FOR (s:Series)    ON (s.name);

// --- 3. 节点存在性约束（可选，Neo4j 5.x 支持） ---

// 确保 Book 节点必须有 title 属性
// (Neo4j 5.8+ property existence constraints)
// CREATE CONSTRAINT book_has_title IF NOT EXISTS FOR (b:Book) REQUIRE b.title IS NOT NULL;

// --- 4. 关系类型说明 ---
//
// 知识图谱包含以下 4 种关系类型：
//
//   (Book)-[:WRITTEN_BY]->(Author)
//     权重: 0.35 — 作者路径，推荐同一作者的其他作品
//
//   (Book)-[:PUBLISHED_BY]->(Publisher)
//     权重: 0.20 — 出版社路径，推荐同一出版社的优质图书
//
//   (Book)-[:HAS_TAG]->(Tag)
//     权重: 0.30 — 标签路径，推荐相同/相似标签的图书
//
//   (Book)-[:BELONGS_TO_SERIES]->(Series)
//     权重: 0.15 — 系列路径，推荐同一系列的其他图书
//
// 这些权重对应概要设计文档第8.2节"知识图谱路径权重计算"，
// 用于在推荐时对不同路径的结果进行加权排序。

// --- 5. 验证 Schema ---
// 执行完成后，运行以下查询验证：

CALL db.schema.visualization();
// 应该看到 5 种节点标签和 4 种关系类型

// 查看所有约束
SHOW CONSTRAINTS;

// 查看所有索引
SHOW INDEXES;

// --- 完成 ---
// Schema 创建完毕。使用 database/import_existing_data.py 导入数据。
