# BookRec — 基于知识图谱的个性化荐书系统

> 前后端分离的全栈项目骨架 · Mock 数据驱动 · 即装即用

---

## 目录

- [项目简介](#项目简介)
- [技术栈](#技术栈)
- [快速开始](#快速开始)
- [项目结构](#项目结构)
- [功能清单（已实现）](#功能清单已实现)
- [功能清单（待实现）](#功能清单待实现)
- [API 接口文档](#api-接口文档)
- [从 Mock 切换到真实数据库](#从-mock-切换到真实数据库)
- [设计规范](#设计规范)
- [开发约定](#开发约定)

---

## 项目简介

BookRec 是一个面向读者的个性化图书推荐平台。核心推荐逻辑基于**协同过滤**和**知识图谱推理**——但当前阶段先不连接数据库，所有数据通过 **前端 Mock 方案** 展示，后端 FastAPI 返回硬编码的 JSON 数据。

项目目标：
- ✅ 阶段一（当前）：完成前后端骨架 + Mock 数据流转，验证页面和交互逻辑
- ⬜ 阶段二：连接 MySQL + Neo4j，接入真实推荐算法
- ⬜ 阶段三：AI 问答助手、用户画像深化、部署上线

> **当前版本**：v1.0.0-mock — 所有数据均为本地模拟，无需任何数据库。

---

## 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 后端框架 | **FastAPI** 0.104+ | Python 3.9+ 异步 Web 框架 |
| 数据校验 | **Pydantic** 2.0+ | 请求/响应模型定义 |
| 认证方案 | **JWT** (python-jose) | 当前返回模拟 Token，未执行真实校验 |
| API 文档 | **Swagger UI** + **ReDoc** | FastAPI 自动生成，`/docs` 或 `/redoc` |
| 前端框架 | **Vue 3** + Composition API | `<script setup>` 语法 |
| UI 组件库 | **Element Plus** 2.4+ | 中文 locale，完整组件体系 |
| 状态管理 | **Pinia** 2.1+ | 用户状态、图书状态 |
| 路由 | **Vue Router** 4.2+ | 7 个页面视图 |
| HTTP 客户端 | **Axios** 1.6+ | 含 Mock 拦截器 |
| 图表 | **ECharts** 5.4+ | 阅读趋势折线图 |
| 构建工具 | **Vite** 5.0+ | 开发服务器 + 生产构建 |

---

## 快速开始

### 环境要求

- **Python** ≥ 3.9
- **Node.js** ≥ 18
- **npm** ≥ 9

### 1. 启动后端

```bash
# 进入后端目录
cd book-recommend-backend

# 安装 Python 依赖
pip install -r requirements.txt

# 启动 FastAPI 开发服务器（端口 8000，热重载）
python run.py
```

启动后访问：
- API 文档（Swagger）：http://localhost:8000/docs
- API 文档（ReDoc）：http://localhost:8000/redoc
- 健康检查：http://localhost:8000/api/v1/health

### 2. 启动前端

打开**另一个终端**：

```bash
# 进入前端目录
cd book-recommend-frontend

# 安装 npm 依赖
npm install

# 启动 Vite 开发服务器（端口 3000，热重载）
npm run dev
```

浏览器打开 **http://localhost:3000** 即可使用。

### 3. 登录测试

| 字段 | 值 |
|------|-----|
| 用户名 | `admin` |
| 密码 | `123456` |

> 其他任意用户名/密码组合会模拟登录失败。

---

## 项目结构

```
book_recommend/
│
├── book-recommend-backend/          # 后端 FastAPI 项目
│   ├── run.py                       # 启动脚本：python run.py
│   ├── requirements.txt             # Python 依赖
│   ├── .env.example                 # 环境变量模板
│   └── app/
│       ├── main.py                  # FastAPI 入口 + CORS 中间件
│       ├── core/
│       │   └── security.py          # JWT 生成/验证（含 TODO 标注）
│       ├── models/
│       │   └── schemas.py           # Pydantic 请求/响应模型
│       ├── routers/
│       │   ├── auth.py              # 登录 / 注册
│       │   ├── books.py             # 图书搜索/详情/推荐/热门/新书
│       │   └── user.py              # 用户画像/评分/行为/书架/评论
│       └── mock_data/               # Mock 数据（替换为数据库后删除）
│           ├── books.py             # 52 本图书数据
│           ├── recommendations.py   # 推荐流数据
│           ├── comments.py          # 评论数据
│           └── shelves.py           # 书架数据
│
├── book-recommend-frontend/         # 前端 Vue 3 项目
│   ├── package.json                 # npm 依赖
│   ├── vite.config.js               # Vite 配置 + 代理
│   ├── index.html                   # HTML 入口
│   ├── .env.development             # 开发环境变量
│   └── src/
│       ├── main.js                  # Vue 应用入口
│       ├── App.vue                  # 根组件（布局路由）
│       ├── router/index.js          # 路由配置（7 个页面）
│       ├── stores/
│       │   ├── user.js              # Pinia 用户状态
│       │   └── book.js              # Pinia 图书状态
│       ├── api/                     # API 层（Mock → 真实后端切换点）
│       │   ├── request.js           # Axios 实例 + Mock 拦截器
│       │   ├── auth.js              # 认证接口
│       │   ├── books.js             # 图书接口
│       │   ├── shelves.js           # 书架接口
│       │   ├── comments.js          # 评论接口
│       │   └── user.js              # 用户接口
│       ├── mock/                    # 前端 Mock 方案
│       │   ├── index.js             # Mock 总出口
│       │   └── data/
│       │       ├── books.js         # 52 本图书 JSON
│       │       ├── recommendations.js # 推荐流/相似/热门/新书
│       │       ├── comments.js      # 评论数据
│       │       ├── shelves.js       # 书架数据
│       │       └── users.js         # 用户信息 + 登录逻辑
│       ├── components/
│       │   ├── common/
│       │   │   ├── Navbar.vue       # 顶部导航栏
│       │   │   ├── Footer.vue       # 底部栏
│       │   │   ├── BookCard.vue     # 图书卡片（多处复用）
│       │   │   └── SkeletonCard.vue # 骨架屏
│       │   ├── home/
│       │   │   ├── FeedList.vue     # 瀑布流推荐列表
│       │   │   └── GuessYouLike.vue # "猜你喜欢"侧边栏
│       │   ├── book/
│       │   │   └── CommentSection.vue # 评论区组件
│       │   └── shelf/
│       │       └── ShelfManager.vue # 书架管理组件
│       └── views/                   # 页面视图
│           ├── Home.vue             # 首页（推荐流 + 侧边栏）
│           ├── Login.vue            # 登录页
│           ├── Register.vue         # 注册页
│           ├── BookDetail.vue       # 图书详情页
│           ├── Shelves.vue          # 书架页
│           ├── Search.vue           # 搜索页
│           └── Profile.vue          # 个人中心（含图表）
```

**统计**：后端 16 个 Python 文件 + 前端 32 个源文件 = **共 48 个核心文件**。后端 API：**22 个接口**。

---

## 功能清单（已实现）

### 📄 页面与交互

| 页面 | 路由 | 功能描述 |
|------|------|----------|
| **登录页** | `/login` | 居中卡片设计，用户名+密码登录，admin/123456 可登录 |
| **注册页** | `/register` | 用户名+邮箱+密码+确认密码，前端校验，模拟注册成功 |
| **首页** | `/` | 欢迎语（根据时段变化），20 本瀑布流推荐卡片，每张带推荐理由，"感兴趣/不感兴趣"按钮，"猜你喜欢"侧边栏 |
| **图书详情** | `/book/:id` | 封面+完整元数据+星级评分+标签，想读/在读/已读一键加入对应书架（自动检测已有书架并高亮），收藏至书架弹窗可选任意书架，AI 推荐理由区，试读弹窗，购书外链下拉菜单，底部评论区 |
| **书架** | `/shelves` | 动态分类切换 + 重命名/删除书架，网格展示 + 进度条，卡片右上角白色「…」菜单（编辑进度 / 移动到其他书架 / 移出书架），新建书架弹窗 |
| **搜索** | `/search?keyword=` | 关键词搜索+结果列表+分页，支持书名/作者/标签搜索 |
| **个人中心** | `/profile` | 侧边栏导航，本周/本月阅读统计卡片，累计阅读天数，ECharts 7 天阅读趋势折线图 |

### 🏷️ UI 特性

- **响应式布局**：桌面端双栏、移动端单栏自动适配
- **骨架屏**：数据加载时显示 SkeletonCard 占位
- **卡片上浮**：hover 时 `translateY(-4px)` + 阴影加深
- **统一配色**：深蓝 `#2C3E50` / 琥珀金 `#D4A24C` / 米白 `#F5F0EB`
- **书架完整管理**：新建/重命名/删除书架，添加/移除/移动图书，编辑阅读进度，移除确认弹窗
- **Element Plus 中文本地化**：所有组件使用中文 locale

### 🔌 后端 API（22 个接口）

| 模块 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 认证 | `POST` | `/api/v1/auth/login` | 登录（admin/123456） |
| 认证 | `POST` | `/api/v1/auth/register` | 注册 |
| 图书 | `GET` | `/api/v1/books/search` | 关键词搜索 + 分页 |
| 图书 | `GET` | `/api/v1/books/{id}` | 图书详情（52 本） |
| 图书 | `GET` | `/api/v1/books/hot` | 热门图书（10 本） |
| 图书 | `GET` | `/api/v1/books/new` | 新书上架（10 本） |
| 推荐 | `GET` | `/api/v1/recommendations/feed` | 个性化推荐流（20 本 + 推荐理由） |
| 推荐 | `GET` | `/api/v1/books/{id}/similar` | 相似图书（6 本） |
| 用户 | `GET` | `/api/v1/user/profile` | 用户画像 + 阅读统计 |
| 评分 | `POST` | `/api/v1/ratings` | 提交评分 |
| 行为 | `POST` | `/api/v1/behaviors/click` | 记录点击行为 |
| 书架 | `GET` | `/api/v1/shelves` | 获取书架列表 |
| 书架 | `POST` | `/api/v1/shelves` | 创建新书架 |
| 书架 | `PUT` | `/api/v1/shelves/{id}` | 重命名书架 |
| 书架 | `DELETE` | `/api/v1/shelves/{id}` | 删除书架（不可删系统默认） |
| 书架 | `POST` | `/api/v1/shelves/items` | 添加图书到书架 |
| 书架 | `PUT` | `/api/v1/shelves/items/{id}` | 编辑进度 / 移动图书到其他书架 |
| 书架 | `PUT` | `/api/v1/shelves/items/{id}/status` | 更新阅读状态（兼容旧接口） |
| 书架 | `DELETE` | `/api/v1/shelves/items/{id}` | 从书架移除图书 |
| 评论 | `GET` | `/api/v1/books/{id}/comments` | 获取图书评论 |
| 评论 | `POST` | `/api/v1/comments` | 发表评论 |
| 评论 | `POST` | `/api/v1/comments/{id}/like` | 点赞评论 |

### 📦 Mock 数据规模

| 数据集 | 数量 | 说明 |
|--------|------|------|
| 图书 | **52 本** | 涵盖科幻、推理、中国文学、外国文学、历史、心理学、计算机、哲学、武侠、传记等 |
| 推荐流 | **20 条** | 每本书附带个性化推荐理由 |
| 评论 | **8 条** | 按图书 ID 可变返回 3-8 条 |
| 书架 | **3+ 个** | 3 个系统书架（想读/在读/已读），支持新建/重命名/删除自定义书架，完整 CRUD |
| 阅读统计 | **7 天** | 用于 ECharts 折线图 | 

---

## 功能清单（待实现）

以下功能在当前 Mock 版本中**暂未实现**，代码中以 `# TODO` 或 `// TODO` 标注：

### 🔗 数据库连接（最高优先级）

| 模块 | 当前状态 | 目标状态 |
|------|----------|----------|
| 用户认证 | Mock 固定账号 admin/123456 | MySQL `users` 表 + bcrypt 密码哈希 |
| JWT 验证 | 跳过真实校验 | 解码 JWT → 查数据库 → 返回用户对象 |
| 图书数据 | 硬编码 52 本 JSON | MySQL `books` / `authors` / `publishers` / `tags` 多表联查 |
| 搜索 | 内存 `filter()` 模糊匹配 | MySQL `LIKE` / 全文索引 或 Elasticsearch |
| 推荐流 | 固定 ID 列表 | 协同过滤 + Neo4j 知识图谱混合推荐 |
| 相似图书 | 固定映射表 | Neo4j `MATCH (b:Book)-[:SIMILAR_TO]->(s:Book)` 图查询 |
| 热门/新书 | 固定 ID 列表 | MySQL 按时间窗口聚合阅读行为数据 |
| 评分 | 打印日志 | MySQL `INSERT INTO ratings` |
| 点击行为 | 打印日志 | MySQL `INSERT INTO user_behaviors` |
| 书架 | 内存数组 | MySQL `shelves` / `shelf_items` 表 CRUD |
| 评论 | 内存数组 | MySQL `comments` 表 + `likes` 计数 |
| 用户画像 | 固定数据 | MySQL 用户偏好标签 + 阅读历史聚合 |

### 🤖 AI 功能（第二阶段）

| 功能 | 说明 |
|------|------|
| **智能图书推荐助手** | AI 对话式图书推荐（本次明确不做） |
| 个性化推荐算法 | 协同过滤 + 知识图谱推理的混合推荐 |
| 用户画像自动更新 | 根据阅读行为动态调整用户偏好权重 |

### 🎨 UI/UX 增强

| 功能 | 说明 |
|------|------|
| 图书封面 | 当前使用 `picsum.photos` 随机占位图，需替换为真实封面图片 |
| 感兴趣/不感兴趣 | 当前仅弹出 Toast，需对接推荐反馈接口 |
| 试读功能 | 当前弹出"开发中"提示，需接入真实试读内容 |
| 购书链接 | 当前拼接搜索 URL 跳转，需替换为真实购买链接 |
| 阅读进度追踪 | 当前显示固定百分比，需接入真实阅读进度记录 |
| 高级搜索 | 当前仅关键词匹配，可增加分类筛选、评分筛选、排序等 |
| 社交功能 | 关注/粉丝、读书笔记、阅读打卡等 |

### 🚀 部署与运维

| 功能 | 说明 |
|------|------|
| 生产构建优化 | 当前 Vite 构建有 chunk 大小警告（Element Plus + ECharts），可按需拆分 |
| Docker 化 | 编写 Dockerfile 和 docker-compose.yml |
| CI/CD | GitHub Actions 自动化测试和部署 |
| 环境配置 | 当前 `.env.example` 未生效，需接入 `python-dotenv` |
| HTTPS / 域名 | 生产环境部署配置 |

---

## API 接口文档

### 统一规范

- **前缀**：`/api/v1`
- **成功响应**：
```json
{
  "code": 200,
  "message": "success",
  "data": { ... }
}
```
- **错误响应**：
```json
{
  "code": 401,
  "message": "用户名或密码错误",
  "data": null
}
```
- **认证方式**：请求头携带 `Authorization: Bearer <token>`
- **分页参数**：`page`（从 1 开始）、`size`（默认 10，最大 50）

### 常用接口示例

<details>
<summary><b>POST /api/v1/auth/login</b> — 登录</summary>

请求：
```json
{ "username": "admin", "password": "123456" }
```

响应：
```json
{
  "code": 200,
  "message": "登录成功",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1...",
    "token_type": "bearer",
    "user": { "id": 1, "username": "admin", "email": "admin@bookrecommend.com", "avatar": "..." }
  }
}
```
</details>

<details>
<summary><b>GET /api/v1/books/search?keyword=三体&page=1&size=10</b> — 搜索图书</summary>

响应：
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "total": 3,
    "page": 1,
    "size": 10,
    "items": [
      { "id": 1, "title": "三体", "cover": "...", "author": "刘慈欣", "rating": 9.3, "rating_count": 285000 }
    ]
  }
}
```
</details>

<details>
<summary><b>GET /api/v1/recommendations/feed</b> — 推荐流（需认证）</summary>

响应：
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "total": 20,
    "items": [
      { "id": 1, "title": "三体", ..., "reason": "📘 因为你喜欢刘慈欣的作品" }
    ]
  }
}
```
</details>

> 完整接口文档请启动后端后访问 http://localhost:8000/docs 查看交互式 Swagger UI。

---

## 从 Mock 切换到真实数据库

### 前端切换

**位置**：`src/api/request.js` 第 5 行

```javascript
const USE_MOCK = true;  // ← 改为 false
```

同时修改各 `src/api/*.js` 文件，将 Mock 函数调用替换为 Axios 请求：

```javascript
// 当前（Mock）：
return mockLogin(username, password)

// 切换后：
return request.post('/auth/login', { username, password })
```

代码中已用 `// TODO: 替换为真实后端 API` 标注所有切换点。

### 后端切换

以图书搜索为例，`app/routers/books.py` 中：

```python
# 当前（Mock）：
result = search_books(keyword=keyword, page=page, size=size)

# 切换后：
# 1. 建立 MySQL 连接
# 2. 执行：SELECT * FROM books WHERE title LIKE '%keyword%' LIMIT size OFFSET ...
# 3. 返回查询结果
```

代码中已用 `# TODO: 替换为真实数据库查询（MySQL/Neo4j）` 标注所有切换点，共 **55 处**。

### 切换步骤

1. 配置 `.env` 文件中的数据库连接信息（MySQL + Neo4j）
2. 创建数据库表结构（参考 `app/models/schemas.py` 中的字段定义）
3. 导入真实图书数据
4. 将前端 `USE_MOCK` 改为 `false`，注释 `mock()` 调用，启用 `request.get/post()`
5. 将后端路由中的 `MOCK_*` 替换为真实数据库查询
6. 测试所有 API 接口
7. 删除 `src/mock/` 和 `app/mock_data/` 目录（或保留作为参考）

---

## 设计规范

| 元素 | 色值 | 用途 |
|------|------|------|
| 主色（深蓝） | `#2C3E50` | 导航栏、标题、主要文字 |
| 主色（墨绿） | `#2E4A3A` | 徽章、辅助色 |
| 背景（米白） | `#F5F0EB` | 页面背景 |
| 背景（浅灰） | `#F8F9FA` | 卡片悬停、区块背景 |
| 强调色（琥珀金） | `#D4A24C` | Logo、推荐理由、评分星、边框 |
| 强调色（暖橙） | `#E67E22` | 进度徽章、点赞激活态 |

### 组件风格

- **卡片**：圆角 12px，阴影 `0 2px 12px rgba(0,0,0,0.08)`，hover 上浮 4px
- **按钮**：Element Plus 默认样式，圆角 4px
- **字体**：PingFang SC / Microsoft YaHei / Helvetica Neue
- **间距**：页面最大宽度 1280px，内容 padding 20px

---

## 开发约定

### TODO 标注规范

项目中所有待完成的工作点均以 `TODO` 标注，共 **75 处**（后端 55 处 + 前端 20 处）：

**后端**（Python）：
```python
# TODO: 替换为真实数据库查询（MySQL/Neo4j）
# 1. 从 MySQL 查询用户评分数据 → 协同过滤
# 2. 从 Neo4j 执行 Cypher 查询 → 知识图谱推理
# 3. 合并排序后返回
```

**前端**（JavaScript/Vue）：
```javascript
// TODO: 后续替换为真实后端 API
// const response = await request.get('/api/v1/recommendations/feed');
```

### Git 工作流（建议）

```
main          ← 生产分支
  └─ develop  ← 开发分支
       ├─ feature/mysql-integration   ← 数据库连接
       ├─ feature/neo4j-graph         ← 知识图谱推荐
       └─ feature/ai-assistant        ← AI 问答助手（阶段三）
```

### 代码规范

- 后端：遵循 PEP 8，类型提示（Type Hints），中文注释
- 前端：ESLint + Prettier（可后续配置），Composition API `<script setup>`
- 命名：前端组件 PascalCase，API 函数 camelCase，后端路由 snake_case

---

## 许可证

本项目仅用于学习和实训目的。

---

> **最后更新**：2024-06-26 · **版本**：v1.0.0-mock · **状态**：可运行
