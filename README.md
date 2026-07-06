# BookRec — 基于知识图谱的个性化图书推荐系统

> Flask + Vue 3 + MySQL + Neo4j + DeepSeek AI

BookRec 是一个集**知识图谱可视化**、**多策略混合推荐**、**AI 智能写作**于一体的个性化图书推荐平台。系统以豆瓣图书数据为基础，构建书籍-作者-标签-出版社知识图谱，融合协同过滤、内容相似、知识图谱路径加权、热门与新书补充五种推荐策略，并接入 DeepSeek 大模型提供 **AI 图图助手**（书籍对话）和 **图图写作**（AI 创作）两大智能功能。

---

## 功能特性

### 📚 图书发现
- **个性化推荐流** — 基于阅读偏好、评分、书架的多策略混合推荐，支持"感兴趣/不感兴趣"实时反馈
- **分类浏览** — 价格（免费/付费）+ 题材标签（古典文学/现代文学/当代文学/外国文学等）组合筛选
- **搜索** — 书名关键词搜索
- **排行榜** — 热门榜、新书榜、免费榜、付费榜、TOP250、现代文学精选
- **知识图谱检索** — 标签筛选 / 自由搜索双模式，ECharts 力导向图可视化，支持一/二级关联深度

### 📖 阅读器
- 分页阅读，自动保存进度
- 字体大小调节，段间距优化
- 免费书全本阅读，付费书试读前 30 页
- 用户创作内容专属阅读器（跳过缓存、独立返回逻辑）

### 👤 用户系统
- JWT + Flask Session 双重认证
- 头像裁剪上传（圆形裁剪 + 实时预览）
- 个人中心：阅读统计（饼图 + 折线图 + 日历热力图）、阅读时长追踪
- 书架管理：想读 / 在读 / 已读，支持自定义书架
- **我的创作** — 独立创作书架，与主页书架隔离，支持作品重命名、换封面、移动、删除

### 🤖 AI 图图助手
- 基于书籍内容的智能对话
- 自动关联当前阅读书籍上下文
- 对话历史持久化，多会话管理

### ✍️ 图图写作（AI 创作）
- **自由创作** — 任意主题的 AI 写作
- **选书创作** — 基于选中书籍的续写、番外、书评
- **草稿箱** — 草稿编辑器、自动保存、追加保存
- **保存到书架** — 创作内容一键出版为书籍，自动生成章节
- **更新至书架** — 修改后同步更新已出版内容

### 🛠️ 管理后台
- **数据总览** — 统计卡片、热门标签词云、最新动态、用户活跃度折线图（日/周/月）
- **图书管理** — CRUD、批量操作
- **用户管理** — 状态筛选、启用/禁用
- **评论管理** — 置顶、删除、搜索
- **知识图谱管理** — Neo4j 图可视化、节点编辑

---

## 技术栈

| 层 | 技术 |
|---|------|
| **前端** | Vue 3 (Composition API) + Vite + Element Plus + ECharts + Pinia |
| **后端** | Flask + PyMySQL + PyJWT + bcrypt |
| **关系数据库** | MySQL 8.0 |
| **图数据库** | Neo4j (Community) |
| **推荐引擎** | 混合推荐 v2：KG (0.30) + CF (0.30) + Content (0.25) + Hot (0.10) + New (0.05) |
| **AI 模型** | DeepSeek API (Chat + Writing) |
| **词云** | ECharts WordCloud (CDN 动态加载) |

---

## 项目结构

```
Book-KnowledgeGraph-Recommendation-master/
├── app.py                          # Flask 后端主程序（API + 业务逻辑）
├── .env                            # 环境变量配置
├── .env.example                    # 环境变量模板
├── book_recommend_dump.sql         # MySQL 示例数据
│
├── database/
│   ├── mysql_schema.sql            # MySQL 表结构
│   └── neo4j_schema.cypher         # Neo4j 图结构
│
├── recommendation/                 # 推荐引擎
│   ├── hybrid_engine.py            # 混合推荐核心
│   ├── kg_recommender.py           # 知识图谱推荐
│   ├── cf_recommender.py           # 协同过滤推荐
│   ├── content_recommender.py      # 内容相似推荐
│   ├── itemcf_recommender.py       # Item-CF 推荐
│   ├── tag_generator.py            # 标签生成
│   └── config.py                   # 推荐配置
│
├── static/                         # 静态资源（头像、封面）
│
└── book_recommend/
    └── book-recommend-frontend/    # Vue 3 前端
        ├── src/
        │   ├── api/                # Axios 请求封装
        │   ├── components/         # 通用组件
        │   │   ├── book/           # 图书相关（评论组件）
        │   │   ├── chat/           # AI 图图聊天组件
        │   │   ├── common/         # 通用（Navbar/Footer/BookCard）
        │   │   ├── home/           # 首页（Feed/Ranking）
        │   │   └── shelf/          # 书架管理
        │   ├── views/              # 页面视图
        │   │   ├── admin/          # 管理后台页面
        │   │   ├── Home.vue        # 首页
        │   │   ├── Reader.vue      # 阅读器
        │   │   ├── Profile.vue     # 个人中心
        │   │   ├── TutuWrite.vue   # 图图写作
        │   │   ├── GraphSearch.vue # 知识图谱检索
        │   │   └── ...
        │   ├── stores/             # Pinia 状态管理
        │   ├── router/             # 路由配置
        │   └── utils/              # 工具函数
        └── public/                 # 静态资源（AI 头像、词云库）
```

---

## 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+
- MySQL 8.0+
- Neo4j 4.x / 5.x / 2025.x (Community)
- DeepSeek API Key

### 1. 克隆项目

```bash
git clone <repo-url>
cd Book-KnowledgeGraph-Recommendation-master
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env`，修改数据库密码和 API Key：

```env
# MySQL
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_mysql_password
MYSQL_DATABASE=book_recommend

# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_neo4j_password

# DeepSeek API
DEEPSEEK_API_KEY=your_api_key
DEEPSEEK_API_BASE=https://api.deepseek.com/v1
```

### 3. 初始化数据库

**MySQL：**

```bash
mysql -u root -p < database/mysql_schema.sql
mysql -u root -p book_recommend < book_recommend_dump.sql   # 导入示例数据
```

**Neo4j：**

启动 Neo4j 后，在 Neo4j Browser 中执行 `database/neo4j_schema.cypher` 创建约束和索引。首次启动 Flask 时会自动从 MySQL 同步图数据。

### 4. 安装 Python 依赖

```bash
pip install flask pymysql neo4j pyjwt bcrypt requests python-dotenv werkzeug
```

### 5. 启动后端

```bash
python app.py
# Flask 运行在 http://localhost:5000
```

### 6. 启动前端

```bash
cd book_recommend/book-recommend-frontend
npm install
npm run dev
# Vite 运行在 http://localhost:3000
```

### 7. 访问

打开浏览器访问 **http://localhost:3000**

---

## 推荐引擎架构

```
用户请求 → HybridRecommender
              ├── KG Recommender      (30%)  知识图谱路径加权
              ├── CF Recommender      (30%)  用户行为协同过滤
              ├── Content Recommender (25%)  标签/作者/描述相似
              ├── Hot Books           (10%)  高分+高票热门保底
              └── New Books            (5%)  新书时效性补充
              → 合并去重 → Top-N 推荐结果
```

推荐理由可解释：每条推荐附带来源标注（如"基于你读过的《xxx》"、"与《xxx》标签相似"、"热门必读"等）。

---

## API 概览

| 前缀 | 说明 |
|------|------|
| `/api/v1/books/*` | 图书列表、详情、搜索、排行榜、个性化推荐 |
| `/api/v1/auth/*` | 登录、注册、头像上传、个人信息 |
| `/api/v1/shelves/*` | 书架管理、图书移动、阅读进度 |
| `/api/v1/user/*` | 用户行为、阅读统计、时长追踪 |
| `/api/v1/tutuWrite/*` | AI 写作会话、消息、草稿箱、出版保存 |
| `/api/v1/admin/*` | 管理后台：概览、图书、用户、评论、知识图谱 |
| `/api/v1/graph/*` | 知识图谱检索、筛选选项 |
| `/api/v1/chat/*` | AI 图图助手对话 |

---

## 数据库设计

### MySQL 核心表

| 表 | 说明 |
|----|------|
| `book` | 图书主表（标题、封面、评分、简介等） |
| `book_chapter` | 章节内容（分页阅读数据） |
| `author` / `book_author` | 作者及图书-作者关联 |
| `tag` / `book_tag` | 标签及图书-标签关联 |
| `user` | 用户表（bcrypt 密码哈希） |
| `bookshelf` / `bookshelf_item` | 书架及书目（支持 `shelf_type` 区分阅读/创作） |
| `comment` | 评论（支持置顶、软删除） |
| `rating` | 评分（1-10 分制） |
| `user_behavior` | 用户行为日志（登录、阅读、评分等） |
| `draft_box` | 草稿箱 |
| `tutuwrite_session` / `tutuwrite_message` | AI 写作会话及消息 |
| `chat_session` / `chat_message` | AI 图图对话会话及消息 |

### Neo4j 图模型

```
(:Book) - [:WRITTEN_BY] → (:Author)
(:Book) - [:HAS_TAG]    → (:Tag)
(:Book) - [:PUBLISHED_BY] → (:Publisher)
```

---

## 数据集

豆瓣图书数据来自[北京大学开放研究数据平台](https://opendata.pku.edu.cn/dataverse/pku)的豆瓣图书评分数据集。

---

## License

本项目仅用于学术研究与学习目的。
