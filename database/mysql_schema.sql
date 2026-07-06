-- ============================================================
-- 基于知识图谱的个性化荐书系统 - MySQL 数据库建表脚本
-- 数据库: book_recommend
-- 版本: 1.0
-- 依据: 04-基于知识图谱的个性化荐书系统-概要设计文档 (第五部分 E-R实体设计)
-- ============================================================

-- 创建数据库
CREATE DATABASE IF NOT EXISTS book_recommend
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;

USE book_recommend;

-- ============================================================
-- 1. 核心主体表
-- ============================================================

-- 1.1 用户表 (USER)
-- 存储所有注册用户的基本信息
CREATE TABLE IF NOT EXISTS `user` (
    `user_id`       BIGINT          NOT NULL AUTO_INCREMENT  COMMENT '用户ID（主键）',
    `username`      VARCHAR(64)     NOT NULL                 COMMENT '用户名',
    `password_hash` VARCHAR(255)    NOT NULL                 COMMENT '加密后的密码（bcrypt）',
    `email`         VARCHAR(128)    DEFAULT NULL             COMMENT '邮箱',
    `phone`         VARCHAR(20)     DEFAULT NULL             COMMENT '手机号',
    `avatar_url`    VARCHAR(512)    DEFAULT NULL             COMMENT '头像URL',
    `role`          ENUM('reader','admin') NOT NULL DEFAULT 'reader' COMMENT '角色：reader=普通用户, admin=管理员',
    `status`        TINYINT         NOT NULL DEFAULT 1       COMMENT '状态：1=正常, 0=禁用',
    `created_at`    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '注册时间',
    `updated_at`    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`user_id`),
    UNIQUE KEY `uk_username` (`username`),
    UNIQUE KEY `uk_email` (`email`),
    KEY `idx_role` (`role`),
    KEY `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

-- 1.2 图书表 (BOOK)
-- 存储所有图书的元数据信息
CREATE TABLE IF NOT EXISTS `book` (
    `book_id`       BIGINT          NOT NULL AUTO_INCREMENT  COMMENT '图书ID（主键）',
    `title`         VARCHAR(255)    NOT NULL                 COMMENT '书名',
    `subtitle`      VARCHAR(255)    DEFAULT NULL             COMMENT '副标题',
    `origin_title`  VARCHAR(255)    DEFAULT NULL             COMMENT '原作名',
    `isbn`          VARCHAR(20)     DEFAULT NULL             COMMENT 'ISBN号',
    `description`   TEXT            DEFAULT NULL             COMMENT '内容简介',
    `cover_url`     VARCHAR(512)    DEFAULT NULL             COMMENT '封面图链接',
    `ebook_url`     VARCHAR(512)    DEFAULT NULL             COMMENT '电子书文件链接',
    `total_pages`   INT             DEFAULT NULL             COMMENT '总页数',
    `price`         DECIMAL(10,2)   DEFAULT NULL             COMMENT '定价',
    `binding`       VARCHAR(32)     DEFAULT NULL             COMMENT '装帧（平装/精装等）',
    `publish_year`  INT             DEFAULT NULL             COMMENT '出版年份',
    `score`         FLOAT           DEFAULT 0                COMMENT '豆瓣评分',
    `votes`         INT             DEFAULT 0                COMMENT '评价人数',
    `douban_id`     BIGINT          DEFAULT NULL             COMMENT '豆瓣编号ID',
    `publisher_id`  BIGINT          DEFAULT NULL             COMMENT '出版社ID',
    `series_id`     BIGINT          DEFAULT NULL             COMMENT '系列ID',
    `language`      VARCHAR(16)     DEFAULT 'zh-CN'          COMMENT '语言',
    `status`        TINYINT         NOT NULL DEFAULT 1       COMMENT '状态：1=上架, 0=下架',
    `created_at`    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '入库时间',
    `updated_at`    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`book_id`),
    UNIQUE KEY `uk_isbn` (`isbn`),
    UNIQUE KEY `uk_douban_id` (`douban_id`),
    KEY `idx_title` (`title`),
    KEY `idx_score` (`score`),
    KEY `idx_publish_year` (`publish_year`),
    KEY `idx_status` (`status`),
    KEY `idx_created_at` (`created_at`),
    FULLTEXT KEY `ft_title_desc` (`title`, `description`)
    -- FK constraints added via ALTER TABLE after publisher/series tables created
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='图书表';

-- ============================================================
-- 2. 图书元数据表
-- ============================================================

-- 2.1 作者表 (AUTHOR)
CREATE TABLE IF NOT EXISTS `author` (
    `author_id`     BIGINT          NOT NULL AUTO_INCREMENT  COMMENT '作者ID（主键）',
    `name`          VARCHAR(128)    NOT NULL                 COMMENT '作者姓名',
    `bio`           TEXT            DEFAULT NULL             COMMENT '生平简介',
    `created_at`    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (`author_id`),
    UNIQUE KEY `uk_name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='作者表';

-- 2.2 图书-作者关联表 (BOOK_AUTHOR) — 多对多桥接表
CREATE TABLE IF NOT EXISTS `book_author` (
    `book_id`       BIGINT          NOT NULL                 COMMENT '图书ID',
    `author_id`     BIGINT          NOT NULL                 COMMENT '作者ID',
    `sort_order`    INT             NOT NULL DEFAULT 0       COMMENT '作者排序（第1作者=0）',
    PRIMARY KEY (`book_id`, `author_id`),
    CONSTRAINT `fk_ba_book`  FOREIGN KEY (`book_id`)   REFERENCES `book`(`book_id`)   ON DELETE CASCADE,
    CONSTRAINT `fk_ba_author` FOREIGN KEY (`author_id`) REFERENCES `author`(`author_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='图书-作者关联表';

-- 2.3 出版社表 (PUBLISHER)
CREATE TABLE IF NOT EXISTS `publisher` (
    `publisher_id`  BIGINT          NOT NULL AUTO_INCREMENT  COMMENT '出版社ID（主键）',
    `name`          VARCHAR(128)    NOT NULL                 COMMENT '出版社名称',
    `address`       VARCHAR(255)    DEFAULT NULL             COMMENT '地址',
    `created_at`    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (`publisher_id`),
    UNIQUE KEY `uk_name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='出版社表';

-- 2.4 标签表 (TAG)
CREATE TABLE IF NOT EXISTS `tag` (
    `tag_id`        BIGINT          NOT NULL AUTO_INCREMENT  COMMENT '标签ID（主键）',
    `name`          VARCHAR(64)     NOT NULL                 COMMENT '标签名称',
    `created_at`    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (`tag_id`),
    UNIQUE KEY `uk_name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='标签表';

-- 2.5 图书-标签关联表 (BOOK_TAG) — 多对多桥接表
CREATE TABLE IF NOT EXISTS `book_tag` (
    `book_id`       BIGINT          NOT NULL                 COMMENT '图书ID',
    `tag_id`        BIGINT          NOT NULL                 COMMENT '标签ID',
    PRIMARY KEY (`book_id`, `tag_id`),
    CONSTRAINT `fk_bt_book` FOREIGN KEY (`book_id`) REFERENCES `book`(`book_id`) ON DELETE CASCADE,
    CONSTRAINT `fk_bt_tag`  FOREIGN KEY (`tag_id`)  REFERENCES `tag`(`tag_id`)   ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='图书-标签关联表';

-- 2.6 系列表 (SERIES)
CREATE TABLE IF NOT EXISTS `series` (
    `series_id`     BIGINT          NOT NULL AUTO_INCREMENT  COMMENT '系列ID（主键）',
    `name`          VARCHAR(128)    NOT NULL                 COMMENT '系列名称',
    `description`   TEXT            DEFAULT NULL             COMMENT '系列简介',
    `created_at`    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (`series_id`),
    UNIQUE KEY `uk_name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='系列表';

-- 添加图书表外键（在 publisher 和 series 表创建之后）
ALTER TABLE `book`
    ADD CONSTRAINT `fk_book_publisher` FOREIGN KEY (`publisher_id`) REFERENCES `publisher`(`publisher_id`) ON DELETE SET NULL;

ALTER TABLE `book`
    ADD CONSTRAINT `fk_book_series`   FOREIGN KEY (`series_id`)    REFERENCES `series`(`series_id`)       ON DELETE SET NULL;

-- ============================================================
-- 3. 用户行为与交互表
-- ============================================================

-- 3.1 用户行为表 (USER_BEHAVIOR)
-- 记录用户所有操作痕迹，用于构建用户画像
CREATE TABLE IF NOT EXISTS `user_behavior` (
    `behavior_id`   BIGINT          NOT NULL AUTO_INCREMENT  COMMENT '行为ID（主键）',
    `user_id`       BIGINT          NOT NULL                 COMMENT '用户ID',
    `action_type`   ENUM('search','view','click','collect','read','rate','comment','share')
                                    NOT NULL                 COMMENT '行为类型',
    `target_type`   ENUM('book','author','tag','series') DEFAULT 'book' COMMENT '目标类型',
    `target_id`     BIGINT          DEFAULT NULL             COMMENT '目标ID',
    `keyword`       VARCHAR(255)    DEFAULT NULL             COMMENT '搜索关键词',
    `duration`      INT             DEFAULT NULL             COMMENT '停留时长（秒）',
    `ip_address`    VARCHAR(45)     DEFAULT NULL             COMMENT '客户端IP',
    `created_at`    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '行为时间',
    PRIMARY KEY (`behavior_id`),
    KEY `idx_user_time` (`user_id`, `created_at`),
    KEY `idx_action_type` (`action_type`),
    KEY `idx_target` (`target_type`, `target_id`),
    CONSTRAINT `fk_ub_user` FOREIGN KEY (`user_id`) REFERENCES `user`(`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户行为表';

-- 3.2 评分表 (RATING)
-- 协同过滤推荐算法的核心数据来源
CREATE TABLE IF NOT EXISTS `rating` (
    `user_id`       BIGINT          NOT NULL                 COMMENT '用户ID',
    `book_id`       BIGINT          NOT NULL                 COMMENT '图书ID',
    `score`         TINYINT         NOT NULL                 COMMENT '评分（1-5星）',
    `created_at`    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '首次评分时间',
    `updated_at`    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '最近更新时间',
    PRIMARY KEY (`user_id`, `book_id`),
    KEY `idx_book_score` (`book_id`, `score`),
    KEY `idx_user_score` (`user_id`, `score`),
    CONSTRAINT `fk_rating_user` FOREIGN KEY (`user_id`) REFERENCES `user`(`user_id`) ON DELETE CASCADE,
    CONSTRAINT `fk_rating_book` FOREIGN KEY (`book_id`) REFERENCES `book`(`book_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='评分表';

-- 3.3 评论表 (COMMENT)
-- 支持楼中楼回复（自关联），Markdown格式
CREATE TABLE IF NOT EXISTS `comment` (
    `comment_id`    BIGINT          NOT NULL AUTO_INCREMENT  COMMENT '评论ID（主键）',
    `user_id`       BIGINT          NOT NULL                 COMMENT '用户ID',
    `book_id`       BIGINT          NOT NULL                 COMMENT '图书ID',
    `parent_id`     BIGINT          DEFAULT NULL             COMMENT '父评论ID（楼中楼回复）',
    `content`       TEXT            NOT NULL                 COMMENT '评论内容（支持Markdown）',
    `likes`         INT             NOT NULL DEFAULT 0       COMMENT '点赞数',
    `status`        ENUM('normal','pinned','deleted') NOT NULL DEFAULT 'normal' COMMENT '评论状态',
    `created_at`    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '发表时间',
    `updated_at`    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`comment_id`),
    KEY `idx_book_status` (`book_id`, `status`, `likes`),
    KEY `idx_user` (`user_id`),
    KEY `idx_parent` (`parent_id`),
    CONSTRAINT `fk_comment_user`   FOREIGN KEY (`user_id`)   REFERENCES `user`(`user_id`)   ON DELETE CASCADE,
    CONSTRAINT `fk_comment_book`   FOREIGN KEY (`book_id`)   REFERENCES `book`(`book_id`)   ON DELETE CASCADE,
    CONSTRAINT `fk_comment_parent` FOREIGN KEY (`parent_id`) REFERENCES `comment`(`comment_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='评论表';

-- 3.4 阅读进度表 (READING_PROGRESS)
-- 实现多端阅读进度同步
CREATE TABLE IF NOT EXISTS `reading_progress` (
    `user_id`       BIGINT          NOT NULL                 COMMENT '用户ID',
    `book_id`       BIGINT          NOT NULL                 COMMENT '图书ID',
    `current_page`  INT             NOT NULL DEFAULT 1       COMMENT '当前页码',
    `progress_pct`  DECIMAL(5,2)    NOT NULL DEFAULT 0.00    COMMENT '进度百分比',
    `updated_at`    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '最近阅读时间',
    PRIMARY KEY (`user_id`, `book_id`),
    KEY `idx_user_updated` (`user_id`, `updated_at`),
    CONSTRAINT `fk_rp_user` FOREIGN KEY (`user_id`) REFERENCES `user`(`user_id`) ON DELETE CASCADE,
    CONSTRAINT `fk_rp_book` FOREIGN KEY (`book_id`) REFERENCES `book`(`book_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='阅读进度表';

-- ============================================================
-- 4. 书架管理表
-- ============================================================

-- 4.1 书架表 (BOOKSHELF)
CREATE TABLE IF NOT EXISTS `bookshelf` (
    `shelf_id`      BIGINT          NOT NULL AUTO_INCREMENT  COMMENT '书架ID（主键）',
    `user_id`       BIGINT          NOT NULL                 COMMENT '用户ID',
    `name`          VARCHAR(64)     NOT NULL                 COMMENT '书架名称（如"想读""在读""已读"）',
    `sort_order`    INT             NOT NULL DEFAULT 0       COMMENT '排序序号',
    `created_at`    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (`shelf_id`),
    UNIQUE KEY `uk_user_shelf` (`user_id`, `name`),
    CONSTRAINT `fk_shelf_user` FOREIGN KEY (`user_id`) REFERENCES `user`(`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='书架表';

-- 4.2 书架条目表 (BOOKSHELF_ITEM) — 书架与图书的多对多桥接表
CREATE TABLE IF NOT EXISTS `bookshelf_item` (
    `shelf_id`      BIGINT          NOT NULL                 COMMENT '书架ID',
    `book_id`       BIGINT          NOT NULL                 COMMENT '图书ID',
    `read_status`   ENUM('want_to_read','reading','finished','classic')
                                    NOT NULL DEFAULT 'want_to_read' COMMENT '阅读状态：想读/在读/已读/经典必读',
    `added_at`      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '加入时间',
    PRIMARY KEY (`shelf_id`, `book_id`),
    KEY `idx_book` (`book_id`),
    KEY `idx_read_status` (`read_status`),
    CONSTRAINT `fk_bsi_shelf` FOREIGN KEY (`shelf_id`) REFERENCES `bookshelf`(`shelf_id`) ON DELETE CASCADE,
    CONSTRAINT `fk_bsi_book`  FOREIGN KEY (`book_id`)  REFERENCES `book`(`book_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='书架条目表';

-- ============================================================
-- 5. 购买与变现表
-- ============================================================

-- 5.1 购书链接表 (PURCHASE_LINK)
CREATE TABLE IF NOT EXISTS `purchase_link` (
    `link_id`       BIGINT          NOT NULL AUTO_INCREMENT  COMMENT '链接ID（主键）',
    `book_id`       BIGINT          NOT NULL                 COMMENT '图书ID',
    `platform`      VARCHAR(32)     NOT NULL                 COMMENT '电商平台（jd/dangdang/taobao等）',
    `url`           VARCHAR(1024)   NOT NULL                 COMMENT '购书链接',
    `price`         DECIMAL(10,2)   DEFAULT NULL             COMMENT '价格',
    `updated_at`    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '价格更新时间',
    PRIMARY KEY (`link_id`),
    UNIQUE KEY `uk_book_platform` (`book_id`, `platform`),
    CONSTRAINT `fk_pl_book` FOREIGN KEY (`book_id`) REFERENCES `book`(`book_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='购书链接表';

-- ============================================================
-- 6. 智能图书推荐助手相关表
-- ============================================================

-- 6.1 对话会话表 (CHAT_SESSION)
CREATE TABLE IF NOT EXISTS `chat_session` (
    `session_id`    BIGINT          NOT NULL AUTO_INCREMENT  COMMENT '会话ID（主键）',
    `user_id`       BIGINT          NOT NULL                 COMMENT '用户ID',
    `title`         VARCHAR(255)    NOT NULL DEFAULT '新对话' COMMENT '会话标题',
    `created_at`    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at`    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '最后活跃时间',
    PRIMARY KEY (`session_id`),
    KEY `idx_user_session` (`user_id`, `updated_at` DESC),
    CONSTRAINT `fk_cs_user` FOREIGN KEY (`user_id`) REFERENCES `user`(`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='对话会话表';

-- 6.2 对话消息表 (CHAT_MESSAGE)
CREATE TABLE IF NOT EXISTS `chat_message` (
    `message_id`    BIGINT          NOT NULL AUTO_INCREMENT  COMMENT '消息ID（主键）',
    `session_id`    BIGINT          NOT NULL                 COMMENT '会话ID',
    `role`          ENUM('user','assistant') NOT NULL        COMMENT '角色：user=用户, assistant=助手',
    `content`       TEXT            NOT NULL                 COMMENT '消息内容',
    `rec_books_json` JSON           DEFAULT NULL             COMMENT '推荐图书ID和理由列表（JSON格式）',
    `created_at`    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '发送时间',
    PRIMARY KEY (`message_id`),
    KEY `idx_session` (`session_id`, `created_at`),
    CONSTRAINT `fk_cm_session` FOREIGN KEY (`session_id`) REFERENCES `chat_session`(`session_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='对话消息表';

-- 6.3 对话反馈表 (CHAT_FEEDBACK)
CREATE TABLE IF NOT EXISTS `chat_feedback` (
    `feedback_id`   BIGINT          NOT NULL AUTO_INCREMENT  COMMENT '反馈ID（主键）',
    `message_id`    BIGINT          NOT NULL                 COMMENT '消息ID',
    `quality_label` ENUM('valid','invalid','needs_improvement') NOT NULL COMMENT '质量标注',
    `notes`         TEXT            DEFAULT NULL             COMMENT '备注',
    `created_at`    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '标注时间',
    PRIMARY KEY (`feedback_id`),
    KEY `idx_quality` (`quality_label`),
    CONSTRAINT `fk_cf_message` FOREIGN KEY (`message_id`) REFERENCES `chat_message`(`message_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='对话反馈表';

-- ============================================================
-- 视图：热门图书 Top 50（近30天评分最高）
-- ============================================================
CREATE OR REPLACE VIEW `v_hot_books` AS
SELECT
    b.book_id,
    b.title,
    b.cover_url,
    b.score,
    b.votes,
    COUNT(DISTINCT r.user_id) AS recent_raters,
    AVG(r.score) AS avg_rating
FROM book b
LEFT JOIN rating r ON b.book_id = r.book_id
    AND r.created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
WHERE b.status = 1
GROUP BY b.book_id
ORDER BY b.score * LOG(b.votes + 1) DESC
LIMIT 50;

-- ============================================================
-- 视图：新书上架（近30天入库）
-- ============================================================
CREATE OR REPLACE VIEW `v_new_books` AS
SELECT book_id, title, cover_url, score, publish_year, created_at
FROM book
WHERE status = 1
ORDER BY created_at DESC
LIMIT 50;

-- ============================================================
-- 完成标记
-- ============================================================
SELECT 'MySQL schema for book_recommend created successfully!' AS status;
