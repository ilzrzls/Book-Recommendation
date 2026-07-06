"""
基于知识图谱的个性化荐书系统 — 完整后端
启动: python app.py  访问: http://localhost:5000
"""
import sys, json, re, bcrypt, jwt
from urllib.parse import quote
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, request, redirect, url_for, session, jsonify, render_template_string
import pymysql

sys.path.insert(0, '.')
from recommendation.config import get_mysql_cfg

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.secret_key = 'book-recommend-secret-2026'
JWT_SECRET = 'book-recommend-jwt-2026'
JWT_ALGORITHM = 'HS256'

import os
os.makedirs('static/covers', exist_ok=True)
os.makedirs('static/avatars', exist_ok=True)

# ═══════════ DB ═══════════
def query(sql, params=None, one=False):
    cfg = get_mysql_cfg()
    conn = pymysql.connect(**cfg, cursorclass=pymysql.cursors.DictCursor, autocommit=True)
    cur = conn.cursor()
    cur.execute(sql, params or ())
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows[0] if (one and rows) else (rows if not one else None)

def execute(sql, params=None):
    cfg = get_mysql_cfg()
    conn = pymysql.connect(**cfg, autocommit=True)
    cur = conn.cursor()
    cur.execute(sql, params or ())
    lid = cur.lastrowid
    cur.close(); conn.close()
    return lid

def create_access_token(user_id):
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(hours=72),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_access_token(token):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload['user_id']
    except:
        return None

def get_user():
    # Check session first
    uid = session.get('user_id')
    if uid:
        u = query("SELECT * FROM user WHERE user_id=%s", (uid,), one=True)
        if u and u.get('status') != 1: return None  # 已禁用
        return u
    # Check JWT Authorization header
    auth = request.headers.get('Authorization', '')
    if auth.startswith('Bearer '):
        uid = verify_access_token(auth[7:])
        if uid:
            u = query("SELECT * FROM user WHERE user_id=%s", (uid,), one=True)
            if u and u.get('status') != 1: return None  # 已禁用
            return u
    return None

def login_required(f):
    @wraps(f)
    def wrap(*a, **kw):
        if not get_user(): return redirect(url_for('login_page'))
        return f(*a, **kw)
    return wrap

_engine = None
def get_engine():
    global _engine
    if _engine is None:
        from recommendation.hybrid_engine import HybridRecommender
        _engine = HybridRecommender()
    return _engine

# ═══════════ CSS ═══════════
CSS = '''<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font:16px/1.6 "Microsoft YaHei","PingFang SC",sans-serif;background:#f5f0eb;color:#2c3e50}
nav{background:#2c3e50;color:#fff;padding:0 20px;display:flex;align-items:center;height:56px;gap:20px}
nav a{color:#ddd;text-decoration:none;font-size:15px}
nav a:hover{color:#fff}
nav .brand{font-size:20px;font-weight:700;color:#d4a24c;margin-right:auto}
nav .user{color:#d4a24c}
.btn{display:inline-block;padding:8px 20px;border-radius:20px;text-decoration:none;font-size:14px;border:none;cursor:pointer;transition:.2s}
.btn-primary{background:#d4a24c;color:#fff}
.btn-outline{border:1px solid #d4a24c;color:#d4a24c;background:transparent}
.btn-sm{padding:4px 12px;font-size:12px}
.btn-danger{background:#e74c3c;color:#fff}
.container{max-width:1200px;margin:0 auto;padding:20px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:16px}
.card{background:#fff;border-radius:10px;padding:18px;box-shadow:0 1px 6px rgba(0,0,0,.06);transition:.2s}
.card:hover{box-shadow:0 3px 16px rgba(0,0,0,.1)}
.card h3{font-size:17px;color:#2e4a3a;margin-bottom:6px}
.card .meta{font-size:12px;color:#888;margin-bottom:3px}
.card .score{display:inline-block;background:#e67e22;color:#fff;padding:2px 8px;border-radius:12px;font-size:13px;margin:6px 0}
.card .desc{font-size:12px;color:#666;line-height:1.5;overflow:hidden;max-height:40px;margin-top:8px}
.card .reason{font-size:11px;color:#d4a24c;margin-top:6px}
.form-card{max-width:400px;margin:60px auto;background:#fff;border-radius:12px;padding:30px;box-shadow:0 2px 12px rgba(0,0,0,.08)}
.form-card input{width:100%;padding:10px 14px;margin:8px 0;border:1px solid #ddd;border-radius:8px;font-size:15px}
.toast{position:fixed;top:20px;right:20px;background:#2e4a3a;color:#fff;padding:10px 20px;border-radius:8px;z-index:999;display:none}
.badge{display:inline-block;padding:2px 10px;border-radius:12px;font-size:12px;background:#f0ede8;color:#888}
.section-title{font-size:20px;color:#2c3e50;margin:20px 0 12px;padding-bottom:8px;border-bottom:2px solid #f0ede8}
.flex-row{display:flex;gap:8px;align-items:center;flex-wrap:wrap}
textarea{font-family:inherit}
</style>'''

NAV = '''<nav><a href="/" class="brand">📖 荐书系统</a><a href="/">首页</a>
{% if user %}<a href="/shelf">我的书架</a><span class="user">{{ user.username }}</span><a href="/logout">退出</a>
{% else %}<a href="/login">登录</a>{% endif %}</nav>
<div id="toast" class="toast"></div><div class="container">'''

FOOT = '''</div><script>
function toast(msg){var t=document.getElementById("toast");t.textContent=msg;t.style.display="block";setTimeout(function(){t.style.display="none"},2000)}
async function api(url,data){var r=await fetch(url,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(data)});return r.json()}
</script></body></html>'''

@app.route('/api/v1/cover/<int:book_id>')
def serve_cover(book_id):
    """从本地提供封面，无效时生成SVG占位图"""
    from flask import Response
    for ext in ('jpg','jpeg','png'):
        path = f'static/covers/{book_id}.{ext}'
        if os.path.exists(path) and os.path.getsize(path) > 2000:
            return app.send_static_file(f'covers/{book_id}.{ext}')
    # 本地无效 → 生成书名占位图
    cur = pymysql.connect(host='localhost',port=3306,user='root',password='123456',database='book_recommend').cursor()
    cur.execute("SELECT title FROM book WHERE book_id=%s", (book_id,))
    row = cur.fetchone()
    cur.close()
    title = row[0] if row else '未知'
    from hashlib import md5
    colors = ['#2C3E50','#8E44AD','#2980B9','#27AE60','#D35400','#C0392B','#16A085','#7F8C8D']
    c = colors[int(md5(str(book_id).encode()).hexdigest(), 16) % len(colors)]
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="240" height="320" viewBox="0 0 240 320">
      <rect width="240" height="320" fill="{c}"/>
      <text x="120" y="150" text-anchor="middle" fill="#fff" font-size="28" font-family="sans-serif">{title[:4]}</text>
      <text x="120" y="185" text-anchor="middle" fill="rgba(255,255,255,0.6)" font-size="14" font-family="sans-serif">暂无封面</text>
    </svg>'''
    return Response(svg, mimetype='image/svg+xml')

def fix_cover(row):
    """优先本地文件，回退代理"""
    if row and row.get('cover'):
        bid = row.get('id') or row.get('book_id')
        if bid:
            for ext in ('jpg','jpeg','png'):
                fpath = f'static/covers/{bid}.{ext}'
                if os.path.exists(fpath) and os.path.getsize(fpath) > 2000:
                    row['cover'] = f'/api/v1/cover/{bid}'
                    return row
        # 本地无效，走代理
        if row['cover'].startswith('http'):
            row['cover'] = f"/api/v1/proxy/image?url={quote(row['cover'], safe='')}"
    return row

def mark_free_books(items):
    """标注书籍是否有章节（免费阅读）并修正封面"""
    if not items: return items
    ids = [b.get('id') or b.get('book_id') for b in items if b.get('id') or b.get('book_id')]
    if ids:
        placeholders = ','.join(['%s'] * len(ids))
        rows = query(f"SELECT DISTINCT book_id FROM book_chapter WHERE book_id IN ({placeholders})", ids)
        chapter_ids = {r['book_id'] for r in rows}
        for b in items:
            bid = b.get('id') or b.get('book_id')
            b['has_chapters'] = bid in chapter_ids
            b['is_free'] = bool(b.get('ebook_url')) or (bid in chapter_ids)
    for b in items:
        fix_cover(b)
    return items

def ok(data=None, msg='ok'):
    return jsonify({'code': 200, 'data': data, 'message': msg})

def err(msg, code=400):
    return jsonify({'code': code, 'data': None, 'message': msg}), code

# ═══════ V1 API (for Vue frontend) ═══════

@app.route('/api/v1/auth/login', methods=['POST'])
def v1_login():
    d = request.get_json()
    u = query("SELECT * FROM user WHERE username=%s", (d.get('username',''),), one=True)
    if u and bcrypt.checkpw(d.get('password','').encode(), u['password_hash'].encode()):
        if u['status'] != 1:
            return err('该账号已被禁用，请联系管理员', 403)
        session['user_id'] = u['user_id']
        token = create_access_token(u['user_id'])
        execute("INSERT INTO user_behavior (user_id,action_type,target_type,target_id,created_at) VALUES (%s,'login','book',0,NOW())", (u['user_id'],))
        return ok({'access_token': token, 'token_type': 'bearer', 'user': {'id': u['user_id'], 'username': u['username'], 'role': u['role'], 'avatar': u.get('avatar_url') or ''}})
    return err('用户名或密码错误', 401)

@app.route('/api/v1/auth/register', methods=['POST'])
def v1_register():
    d = request.get_json()
    if query("SELECT user_id FROM user WHERE username=%s", (d.get('username',''),), one=True):
        return err('用户名已存在')
    h = bcrypt.hashpw(d.get('password','').encode(), bcrypt.gensalt()).decode()
    uid = execute("INSERT INTO user (username, password_hash, role) VALUES (%s,%s,'reader')",
                  (d['username'], h))
    return ok({'user_id': uid})

@app.route('/api/v1/auth/logout', methods=['POST'])
def v1_logout():
    session.pop('user_id', None)
    return ok({'message': '已退出登录'})

@app.route('/api/v1/auth/profile')
def v1_profile():
    u = get_user()
    if not u: return err('请登录', 401)

    # 书架统计
    shelf_stats = query("SELECT read_status, COUNT(*) AS n FROM bookshelf_item bsi JOIN bookshelf bs ON bsi.shelf_id=bs.shelf_id WHERE bs.user_id=%s GROUP BY read_status", (u['user_id'],))
    shelf_counts = {s['read_status']: s['n'] for s in shelf_stats}

    total_books = sum(shelf_counts.values())
    finished_books = shelf_counts.get('finished', 0)

    # 偏好标签分布（用户书架中所有图书的标签统计）
    tag_dist = query("""
        SELECT t.name, COUNT(*) AS cnt FROM bookshelf_item bsi
        JOIN bookshelf bs ON bsi.shelf_id=bs.shelf_id
        JOIN book_tag bt ON bsi.book_id=bt.book_id
        JOIN tag t ON bt.tag_id=t.tag_id
        WHERE bs.user_id=%s
        GROUP BY t.name ORDER BY cnt DESC LIMIT 12
    """, (u['user_id'],))
    tag_distribution = [{'name': t['name'], 'count': t['cnt']} for t in tag_dist]

    reading_stats = {
        'total_books': total_books,
        'finished_books': finished_books,
        'tag_count': len(tag_distribution),
        'tag_distribution': tag_distribution,
    }

    return ok({
        'username': u['username'], 'email': u['email'] or '', 'role': u['role'],
        'avatar': u.get('avatar_url') or '',
        'shelf': shelf_counts,
        'reading_stats': reading_stats,
    })

from werkzeug.utils import secure_filename
ALLOWED_AVATAR_EXTS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

@app.route('/api/v1/auth/avatar', methods=['POST'])
def v1_upload_avatar():
    u = get_user()
    if not u: return err('请登录', 401)
    file = request.files.get('file')
    if not file or file.filename == '':
        return err('请选择图片文件')
    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    if ext not in ALLOWED_AVATAR_EXTS:
        return err('图片格式仅支持: png, jpg, jpeg, gif, webp')
    import uuid
    filename = f"avatar_{u['user_id']}_{uuid.uuid4().hex[:8]}.{ext}"
    filepath = os.path.join('static', 'avatars', filename)
    file.save(filepath)
    avatar_url = f'/static/avatars/{filename}'
    execute("UPDATE user SET avatar_url=%s WHERE user_id=%s", (avatar_url, u['user_id']))
    return ok({'avatar_url': avatar_url})

@app.route('/api/v1/books/search')
def v1_search():
    kw = request.args.get('keyword','')
    tags_str = request.args.get('tags','')
    page = int(request.args.get('page',1))
    size = int(request.args.get('size',10))
    off = (page-1)*size

    # 处理标签筛选
    tag_list = [t.strip() for t in tags_str.split(',') if t.strip()] if tags_str else []
    has_free = '免费' in tag_list
    has_paid = '付费' in tag_list
    normal_tags = [t for t in tag_list if t not in ('免费','付费')]

    if kw or normal_tags or has_free or has_paid:
        base_sql = "SELECT DISTINCT b.book_id AS id, b.title, b.score AS rating, COALESCE(b.score,0) AS score, b.description, b.cover_url AS cover, b.votes AS rating_count FROM book b"
        joins = []
        wheres = ["b.status=1", "b.description NOT LIKE %s"]
        params = ['用户创作%']

        if kw:
            wheres.append("(b.title LIKE %s OR b.description LIKE %s)")
            params.extend([f"%{kw}%", f"%{kw}%"])

        if normal_tags:
            joins.append("JOIN book_tag bt ON b.book_id=bt.book_id JOIN tag t ON bt.tag_id=t.tag_id")
            ph = ','.join(['%s'] * len(normal_tags))
            wheres.append(f"t.name IN ({ph})")
            params.extend(normal_tags)

        # 免费/付费
        FREE_COND = "(b.ebook_url IS NOT NULL AND b.ebook_url != '' OR b.book_id IN (SELECT DISTINCT book_id FROM book_chapter))"
        PAID_COND = "(b.ebook_url IS NULL OR b.ebook_url = '') AND b.book_id NOT IN (SELECT DISTINCT book_id FROM book_chapter)"
        if has_free: wheres.append(FREE_COND)
        elif has_paid: wheres.append(PAID_COND)

        sql = f"{base_sql} {' '.join(joins)} WHERE {' AND '.join(wheres)} ORDER BY b.score DESC LIMIT %s OFFSET %s"
        params.extend([size, off])
        books = query(sql, params)

        # count
        cnt_sql = f"SELECT COUNT(DISTINCT b.book_id) AS n FROM book b {' '.join(joins)} WHERE {' AND '.join(wheres)}"
        total = query(cnt_sql, params[:-2], one=True)['n']
    else:
        books = query("SELECT book_id AS id, title, score AS rating, COALESCE(score,0) AS score, description, cover_url AS cover, votes AS rating_count FROM book ORDER BY score DESC LIMIT %s OFFSET %s", (size, off))
        total = query("SELECT COUNT(*) AS n FROM book", one=True)['n']
    return ok({'items': mark_free_books(books), 'total': total, 'page': page, 'size': size})

@app.route('/api/v1/books/<int:book_id>')
def v1_book_detail(book_id):
    b = query("SELECT b.*, a.name AS author, p.name AS publisher FROM book b LEFT JOIN book_author ba ON b.book_id=ba.book_id AND ba.sort_order=0 LEFT JOIN author a ON ba.author_id=a.author_id LEFT JOIN publisher p ON b.publisher_id=p.publisher_id WHERE b.book_id=%s", (book_id,), one=True)
    if not b: return err('Not found', 404)
    all_tags = query("SELECT t.tag_id AS id, t.name FROM book_tag bt JOIN tag t ON bt.tag_id=t.tag_id WHERE bt.book_id=%s", (book_id,))
    all_authors = query("SELECT a.author_id AS id, a.name FROM book_author ba JOIN author a ON ba.author_id=a.author_id WHERE ba.book_id=%s ORDER BY ba.sort_order", (book_id,))
    comments = query("SELECT c.comment_id AS id, COALESCE(NULLIF(c.nickname,''), COALESCE(u.username,'豆瓣书友')) AS user_name, c.content, c.likes, COALESCE(c.comment_date, CAST(c.created_at AS CHAR)) AS created_at, CASE WHEN c.nickname IS NOT NULL AND c.nickname!='' THEN '' ELSE COALESCE(u.avatar_url,'') END AS user_avatar FROM comment c LEFT JOIN user u ON c.user_id=u.user_id WHERE c.book_id=%s AND c.status='normal' ORDER BY c.likes DESC LIMIT 10", (book_id,))
    # 阅读统计
    shelf_stats = query("""
        SELECT bsi.read_status, COUNT(*) AS n FROM bookshelf_item bsi
        JOIN bookshelf bs ON bsi.shelf_id=bs.shelf_id
        WHERE bsi.book_id=%s GROUP BY bsi.read_status
    """, (book_id,))
    want_cnt = b.get('douban_want_count') or 0
    reading_cnt = b.get('douban_reading_count') or 0
    read_cnt = b.get('douban_read_count') or 0
    desc = b.get('description') or ''
    subtitle = b.get('subtitle') or ''
    data = {
        'id': b['book_id'], 'title': b['title'], 'subtitle': subtitle,
        'author': all_authors[0]['name'] if all_authors else '',
        'authors': [{'id': a['id'], 'name': a['name']} for a in all_authors],
        'publisher': {'id': b.get('publisher_id'), 'name': b.get('publisher') or ''},
        'rating': b['score'] or 0, 'score': b['score'] or 0, 'isbn': b.get('isbn'),
        'description': desc, 'summary': desc,
        'cover': b.get('cover_url'),
        'pages': b.get('total_pages'), 'binding': b.get('binding'),
        'publish_date': str(b.get('publish_year')) if b.get('publish_year') else '',
        'publish_year': b.get('publish_year'),
        'price': float(b['price']) if b.get('price') else 0,
        'rating_count': b.get('votes') or 0,
        'douban_id': b.get('douban_id'),
        'tags': [{'id': t['id'], 'name': t['name']} for t in all_tags],
        'comments': list(comments),
        'want_count': want_cnt, 'reading_count': reading_cnt, 'read_count': read_cnt,
    }
    return ok(fix_cover(data))

import random as _random
REASON_LABELS = ['豆瓣高分推荐', '读者热评佳作', '经典必读之选', '口碑爆棚好书', '畅销不衰名作', '书友力荐精品', '年度最受欢迎', '备受好评佳作', '不可错过的经典', '值得一读再读']
KG_REASONS = ['同作者作品', '同类标签好书', '知识图谱关联', '相似风格推荐', '书友也在读']

@app.route('/api/v1/books/feed')
def v1_feed():
    u = get_user()
    if u:
        # ── 策略1: 混合推荐引擎 (KG + CF + Content + Hot) ──
        try:
            engine = get_engine()
            # 获取用户已交互的书（用于排除）
            exclude = set(r['book_id'] for r in query(
                "SELECT DISTINCT bsi.book_id FROM bookshelf_item bsi "
                "JOIN bookshelf bs ON bsi.shelf_id=bs.shelf_id WHERE bs.user_id=%s", (u['user_id'],)))
            # 排除用户标记为"不感兴趣"的书
            exclude |= set(r['target_id'] for r in query(
                "SELECT DISTINCT target_id FROM user_behavior "
                "WHERE user_id=%s AND action_type='not_interested'", (u['user_id'],)))
            recs = engine.homepage_recommend(user_id=u['user_id'], top_n=20, exclude_ids=list(exclude))
            if recs:
                items = []
                for r in recs:
                    douban_id = r.get('douban_id')
                    if douban_id:
                        b = query("SELECT book_id AS id, title, score AS rating, COALESCE(score,0) AS score, "
                                  "description, cover_url AS cover, votes AS rating_count "
                                  "FROM book WHERE douban_id=%s", (str(douban_id),), one=True)
                        # 二次过滤：确保不在用户书架中
                        if b and b['id'] not in exclude:
                            items.append(fix_cover({**b, 'reason': r.get('reason', '混合推荐')}))
                if items:
                    return ok({'items': mark_free_books(items[:18]), 'personalized': True, 'method': 'hybrid_cf'})
        except Exception as e:
            print(f"  Feed hybrid error: {e}")

    # 未登录 → 热门推荐
    hot = query("SELECT book_id AS id, title, score AS rating, COALESCE(score,0) AS score, description, cover_url AS cover, votes AS rating_count FROM book WHERE status=1 AND description NOT LIKE '用户创作%%' ORDER BY score DESC LIMIT 18")
    items = []
    REASON_LABELS = ['经典必读', '热门推荐', '高分好评', '口碑佳作', '畅销书籍']
    for i, x in enumerate(hot):
        reason = REASON_LABELS[i % len(REASON_LABELS)]
        items.append({**x, 'reason': reason})
    return ok({'items': mark_free_books(items), 'personalized': False})

@app.route('/api/v1/books/top')
def v1_top():
    # 按 book_id 升序 = 豆瓣 Top250 原始爬取顺序
    books = query("SELECT book_id AS id, title, score AS rating, cover_url AS cover FROM book WHERE status=1 AND description NOT LIKE '用户创作%%' ORDER BY book_id ASC LIMIT 20")
    return ok({'items': [fix_cover(b) for b in books]})

@app.route('/api/v1/books/<int:book_id>/similar')
def v1_similar(book_id):
    try:
        engine = get_engine()
        recs = engine.similar_books(book_id, 8)  # 混合推荐（KG + 内容）
        items = []
        for r in recs:
            b = query("SELECT book_id AS id, title, COALESCE(score,0) AS rating, cover_url AS cover FROM book WHERE douban_id=%s AND description NOT LIKE '用户创作%%'", (r['douban_id'],), one=True)
            if b: items.append(fix_cover({**b, 'reason': r.get('reason',''), 'similarity': r.get('score',0)}))
        return ok({'items': mark_free_books(items)})
    except: return ok({'items': []})

# ═══════ V1 Reading Progress API ═══════

@app.route('/api/v1/user/progress', methods=['POST'])
def v1_save_progress():
    u = get_user()
    if not u: return err('请登录', 401)
    d = request.get_json()
    book_id = d.get('book_id')
    current_page = d.get('current_page', 0)
    progress_pct = d.get('progress_pct', 0)
    execute("""INSERT INTO reading_progress (user_id, book_id, current_page, progress_pct)
        VALUES (%s,%s,%s,%s) ON DUPLICATE KEY UPDATE current_page=%s, progress_pct=%s""",
        (u['user_id'], book_id, current_page, progress_pct, current_page, progress_pct))
    # 仅系统书架更新阅读状态
    sid = query("SELECT bs.shelf_id, bs.name FROM bookshelf bs JOIN bookshelf_item bsi ON bs.shelf_id=bsi.shelf_id WHERE bs.user_id=%s AND bsi.book_id=%s",
                (u['user_id'], book_id), one=True)
    if sid and sid['name'] in ('想读', '在读', '已读'):
        execute("UPDATE bookshelf_item SET read_status='reading' WHERE shelf_id=%s AND book_id=%s",
                (sid['shelf_id'], book_id))
    return ok({'book_id': book_id, 'current_page': current_page, 'progress_pct': progress_pct})

@app.route('/api/v1/user/progress/<int:book_id>')
def v1_get_progress(book_id):
    u = get_user()
    if not u: return err('请登录', 401)
    p = query("SELECT current_page, progress_pct, updated_at FROM reading_progress WHERE user_id=%s AND book_id=%s",
              (u['user_id'], book_id), one=True)
    if p:
        return ok({'book_id': book_id, 'current_page': p['current_page'], 'progress_pct': float(p['progress_pct']), 'updated_at': str(p['updated_at'])})
    return ok({'book_id': book_id, 'current_page': 0, 'progress_pct': 0})

@app.route('/api/v1/user/progress')
def v1_list_progress():
    u = get_user()
    if not u: return err('请登录', 401)
    rows = query("""SELECT rp.book_id, rp.current_page, rp.progress_pct, rp.updated_at, b.title, b.cover_url
        FROM reading_progress rp JOIN book b ON rp.book_id=b.book_id
        WHERE rp.user_id=%s ORDER BY rp.updated_at DESC LIMIT 30""", (u['user_id'],))
    return ok({'items': [{'book_id': r['book_id'], 'title': r['title'],
        'cover': r['cover_url'], 'current_page': r['current_page'],
        'progress_pct': float(r['progress_pct']), 'updated_at': str(r['updated_at'])} for r in rows]})

# ── 阅读时长 ──

@app.route('/api/v1/user/reading-time', methods=['POST'])
def v1_save_reading_time():
    u = get_user()
    if not u: return err('请登录', 401)
    d = request.get_json()
    book_id = d.get('book_id')
    duration = max(0, int(d.get('duration_seconds', 0)))
    # 仅免费图书计入
    is_free = query("""SELECT (b.ebook_url IS NOT NULL AND b.ebook_url != ''
            OR b.book_id IN (SELECT DISTINCT book_id FROM book_chapter)) AS free
        FROM book b WHERE b.book_id=%s""", (book_id,), one=True)
    if not is_free or not is_free['free']:
        return ok({'book_id': book_id, 'duration_seconds': 0, 'skipped': True, 'reason': '付费图书不计阅读时长'})
    today = datetime.now().strftime('%Y-%m-%d')
    execute("""INSERT INTO reading_time_log (user_id, book_id, reading_date, duration_seconds)
        VALUES (%s,%s,%s,%s)
        ON DUPLICATE KEY UPDATE duration_seconds = duration_seconds + %s""",
        (u['user_id'], book_id, today, duration, duration))
    return ok({'book_id': book_id, 'duration_seconds': duration, 'date': today})

@app.route('/api/v1/user/reading-stats')
def v1_reading_stats():
    u = get_user()
    if not u: return err('请登录', 401)
    period = request.args.get('period', 'daily')
    if period == 'daily':
        # 当月每日阅读时长 + 每日下每本书明细
        year = int(request.args.get('year', datetime.now().year))
        month = int(request.args.get('month', datetime.now().month))
        rows = query("""SELECT reading_date, book_id, duration_seconds
            FROM reading_time_log WHERE user_id=%s
            AND YEAR(reading_date)=%s AND MONTH(reading_date)=%s
            ORDER BY reading_date""", (u['user_id'], year, month))
        days_map = {}
        for r in rows:
            dk = str(r['reading_date'])
            if dk not in days_map:
                days_map[dk] = {'date': dk, 'total_seconds': 0, 'books': {}}
            days_map[dk]['total_seconds'] += r['duration_seconds']
            days_map[dk]['books'][str(r['book_id'])] = r['duration_seconds']
        return ok({'period': 'daily', 'year': year, 'month': month,
            'days': list(days_map.values())})
    elif period == 'weekly':
        year = int(request.args.get('year', datetime.now().year))
        month = int(request.args.get('month', datetime.now().month))
        rows = query("""SELECT reading_date, SUM(duration_seconds) AS total
            FROM reading_time_log WHERE user_id=%s
            AND YEAR(reading_date)=%s AND MONTH(reading_date)=%s
            GROUP BY reading_date ORDER BY reading_date""", (u['user_id'], year, month))
        # 按周分组（ISO 周）
        from collections import defaultdict
        weeks = defaultdict(int)
        for r in rows:
            d = datetime.strptime(str(r['reading_date']), '%Y-%m-%d')
            week_key = d.strftime('%Y-W%W')
            weeks[week_key] += int(r['total'] or 0)
        # 计算每周起止日期
        week_list = []
        for wk in sorted(weeks.keys()):
            y, w = wk.split('-W')
            w = int(w)
            from datetime import timedelta
            jan4 = datetime(int(y), 1, 4)
            start = jan4 - timedelta(days=jan4.weekday()) + timedelta(weeks=w-1)
            end = start + timedelta(days=6)
            week_list.append({'week_start': start.strftime('%Y-%m-%d'),
                'week_end': end.strftime('%Y-%m-%d'), 'total_seconds': weeks[wk]})
        return ok({'period': 'weekly', 'year': year, 'month': month, 'weeks': week_list})
    elif period == 'monthly':
        year = int(request.args.get('year', datetime.now().year))
        rows = query("""SELECT MONTH(reading_date) AS m, SUM(duration_seconds) AS total
            FROM reading_time_log WHERE user_id=%s AND YEAR(reading_date)=%s
            GROUP BY MONTH(reading_date) ORDER BY m""", (u['user_id'], year))
        months = []
        for r in rows:
            months.append({'month': f"{year}-{r['m']:02d}", 'total_seconds': int(r['total'] or 0)})
        return ok({'period': 'monthly', 'year': year, 'months': months})
    return err('period 参数无效，可选 daily/monthly')

@app.route('/api/v1/user/reading-stats/detail')
def v1_reading_stats_detail():
    u = get_user()
    if not u: return err('请登录', 401)
    date_str = request.args.get('date', '')
    rows = query("""SELECT rtl.book_id, rtl.duration_seconds, b.title, b.cover_url
        FROM reading_time_log rtl JOIN book b ON rtl.book_id=b.book_id
        WHERE rtl.user_id=%s AND rtl.reading_date=%s
        ORDER BY rtl.duration_seconds DESC""", (u['user_id'], date_str))
    total_sec = sum(r['duration_seconds'] for r in rows)
    books_out = []
    for r in rows:
        bd = {'book_id': r['book_id'], 'title': r['title'],
              'cover': r['cover_url'] or '', 'duration_seconds': r['duration_seconds']}
        fix_cover(bd)
        books_out.append(bd)
    return ok({'date': date_str, 'total_seconds': total_sec, 'books': books_out})

# ═══════ V1 在线阅读 API ═══════

@app.route('/api/v1/books/<int:book_id>/chapters')
def v1_chapters(book_id):
    chapters = query("""
        SELECT chapter_id, chapter_no, chapter_name, chapter_order, word_count,
               COALESCE(CHAR_LENGTH(content), 0) AS char_count
        FROM book_chapter WHERE book_id=%s ORDER BY chapter_order
    """, (book_id,))
    total_chars = sum(c['char_count'] for c in chapters)
    return ok({
        'book_id': book_id,
        'total': len(chapters),
        'total_chars': total_chars,
        'chapters': [{'id': c['chapter_id'], 'no': c['chapter_no'],
            'name': c['chapter_name'], 'order': c['chapter_order'],
            'word_count': c['word_count'], 'char_count': c['char_count']} for c in chapters]
    })

@app.route('/api/v1/books/<int:book_id>/chapters/<int:chapter_order>')
def v1_chapter_content(book_id, chapter_order):
    u = get_user()
    ch = query("""SELECT chapter_id, chapter_no, chapter_name, chapter_order,
        content, word_count FROM book_chapter
        WHERE book_id=%s AND chapter_order=%s""", (book_id, chapter_order), one=True)
    if not ch: return err('章节不存在', 404)

    content = ch['content'] or ''
    total_chars = len(content)
    is_limited = False

    # 未登录用户：整本书累计只能试读 8000 字（约10页）
    if not u:
        # 用 session 追踪累计已读字符数
        trial_key = f'trial_chars_book_{book_id}'
        cumulative = session.get(trial_key, 0)
        TRIAL_LIMIT = 8000

        if cumulative >= TRIAL_LIMIT:
            return err('试读仅限10页，已读完。请登录后继续阅读全文。', 403)

        remaining = TRIAL_LIMIT - cumulative
        if total_chars > remaining:
            content = content[:remaining] + '\n\n——— 试读已达10页上限，登录后可阅读全文 ———'
            is_limited = True
            session[trial_key] = TRIAL_LIMIT  # 标记已达上限
        else:
            session[trial_key] = cumulative + total_chars

    # 记录阅读行为
    if u:
        try:
            total_chs = query('SELECT MAX(chapter_order) as m FROM book_chapter WHERE book_id=%s', (book_id,), one=True)
            max_order = total_chs['m'] if total_chs else 1
            execute("""INSERT INTO reading_progress (user_id, book_id, current_page, progress_pct)
                VALUES (%s,%s,%s,%s) ON DUPLICATE KEY UPDATE current_page=%s, progress_pct=%s""",
                (u['user_id'], book_id, chapter_order, min(100, int((chapter_order + 1) * 100 / max(1, max_order + 1))),
                 chapter_order, min(100, int((chapter_order + 1) * 100 / max(1, max_order + 1)))))
        except: pass

    return ok({
        'chapter_id': ch['chapter_id'], 'chapter_no': ch['chapter_no'],
        'chapter_name': ch['chapter_name'], 'chapter_order': ch['chapter_order'],
        'word_count': ch['word_count'], 'content': content,
        'total_chars': total_chars, 'is_limited': is_limited
    })

@app.route('/api/v1/tags')
def v1_tags():
    tags = query("SELECT tag_id AS id, name FROM tag ORDER BY name")
    return ok({'items': [{'id': t['id'], 'name': t['name']} for t in tags]})

@app.route('/api/v1/books/hot')
def v1_hot():
    b = query("SELECT book_id AS id, title, score AS rating, COALESCE(score,0) AS score, description, cover_url AS cover, votes AS rating_count FROM book WHERE description NOT LIKE '用户创作%%' ORDER BY score DESC LIMIT 15")
    return ok({'items': mark_free_books(b)})

@app.route('/api/v1/books/new')
def v1_new():
    b = query("SELECT book_id AS id, title, score AS rating, COALESCE(score,0) AS score, description, cover_url AS cover, votes AS rating_count FROM book WHERE description NOT LIKE '用户创作%%' ORDER BY created_at DESC LIMIT 15")
    return ok({'items': mark_free_books(b)})

@app.route('/api/v1/books/free-rank')
def v1_free_rank():
    """免费榜：有电子书或章节的图书，按评分降序"""
    b = query("""
        SELECT b.book_id AS id, b.title, b.score AS rating, COALESCE(b.score,0) AS score,
               b.description, b.cover_url AS cover, b.votes AS rating_count
        FROM book b
        WHERE b.status=1 AND b.description NOT LIKE '用户创作%%' AND (
            (b.ebook_url IS NOT NULL AND b.ebook_url != '')
            OR b.book_id IN (SELECT DISTINCT book_id FROM book_chapter)
        )
        ORDER BY b.score DESC LIMIT 15
    """)
    return ok({'items': mark_free_books(b)})

@app.route('/api/v1/books/paid-rank')
def v1_paid_rank():
    """付费榜：无电子书且无章节的图书，按评分降序"""
    b = query("""
        SELECT b.book_id AS id, b.title, b.score AS rating, COALESCE(b.score,0) AS score,
               b.description, b.cover_url AS cover, b.votes AS rating_count
        FROM book b
        WHERE b.status=1 AND b.description NOT LIKE '用户创作%%' AND (
            b.ebook_url IS NULL OR b.ebook_url = ''
        ) AND b.book_id NOT IN (SELECT DISTINCT book_id FROM book_chapter)
        ORDER BY b.score DESC LIMIT 15
    """)
    return ok({'items': mark_free_books(b)})

@app.route('/api/v1/books/modern-literature')
def v1_modern_literature():
    """现代文学榜：标签含文学类的图书，按评分降序"""
    b = query("""
        SELECT b.book_id AS id, b.title, b.score AS rating, COALESCE(b.score,0) AS score,
               b.description, b.cover_url AS cover, b.votes AS rating_count
        FROM book b
        JOIN book_tag bt ON b.book_id = bt.book_id
        JOIN tag t ON bt.tag_id = t.tag_id
        WHERE b.status=1 AND b.description NOT LIKE '用户创作%%' AND t.name IN ('文学','小说','中国文学','现代文学','外国文学','经典')
        GROUP BY b.book_id
        ORDER BY b.score DESC LIMIT 15
    """)
    return ok({'items': mark_free_books(b)})

@app.route('/api/v1/user/profile', methods=['GET', 'PUT'])
def v1_user_profile():
    u = get_user()
    if not u: return err('请登录', 401)
    if request.method == 'PUT':
        d = request.get_json()
        new_username = (d.get('username') or '').strip()
        if not new_username:
            return err('用户名不能为空', 400)
        if len(new_username) > 20:
            return err('用户名不超过20个字符', 400)
        # 检查是否与其他用户重复
        exist = query("SELECT user_id FROM user WHERE username=%s AND user_id!=%s", (new_username, u['user_id']), one=True)
        if exist:
            return err('该用户名已被使用', 409)
        execute("UPDATE user SET username=%s WHERE user_id=%s", (new_username, u['user_id']))
        return ok({'username': new_username})
    shelf = query("SELECT b.book_id AS id, b.title, bsi.read_status FROM bookshelf_item bsi JOIN bookshelf bs ON bsi.shelf_id=bs.shelf_id JOIN book b ON bsi.book_id=b.book_id WHERE bs.user_id=%s", (u['user_id'],))
    return ok({'username': u['username'], 'email': u['email'], 'shelf': list(shelf)})

@app.route('/api/v1/user/rating', methods=['POST'])
def v1_rate():
    u = get_user()
    if not u: return err('请登录', 401)
    d = request.get_json()
    score = int(d.get('score', 0))
    if score < 1 or score > 10: return err('评分须在1-10之间', 400)
    execute("REPLACE INTO rating (user_id, book_id, score, created_at) VALUES (%s,%s,%s,NOW())", (u['user_id'], d['book_id'], score))
    return ok()

@app.route('/api/v1/user/click', methods=['POST'])
def v1_click():
    u = get_user()
    if u:
        d = request.get_json()
        execute("INSERT INTO user_behavior (user_id, action_type, target_type, target_id) VALUES (%s,'click','book',%s)", (u['user_id'], d.get('book_id')))
    return ok()

@app.route('/api/v1/user/feedback', methods=['POST'])
def v1_feedback():
    u = get_user()
    if not u: return err('请登录', 401)
    d = request.get_json()
    action = 'interested' if d.get('interested') else 'not_interested'
    execute("INSERT INTO user_behavior (user_id, action_type, target_type, target_id) VALUES (%s,%s,'book',%s)",
            (u['user_id'], action, d.get('book_id')))
    return ok({'recorded': True})

@app.route('/api/v1/user/comments')
def v1_user_comments():
    u = get_user()
    if not u: return err('请登录', 401)
    comments = query("""
        SELECT c.comment_id AS id, c.content, c.likes,
               COALESCE(c.comment_date, CAST(c.created_at AS CHAR)) AS created_at,
               b.book_id, b.title AS book_title, b.cover_url AS book_cover,
               COALESCE(u2.avatar_url,'') AS user_avatar
        FROM comment c
        JOIN book b ON c.book_id = b.book_id
        LEFT JOIN user u2 ON c.user_id = u2.user_id
        WHERE c.user_id = %s AND c.status = 'normal'
        ORDER BY c.created_at DESC LIMIT 50
    """, (u['user_id'],))
    return ok({'items': [{
        'id': c['id'], 'content': c['content'], 'likes': c['likes'],
        'created_at': c['created_at'],
        'book_id': c['book_id'], 'book_title': c['book_title'],
        'book_cover': fix_cover({'cover': c.get('book_cover', ''), 'id': c['book_id']})['cover'],
        'user_avatar': c.get('user_avatar', ''),
    } for c in comments]})

@app.route('/api/v1/comments/book/<int:book_id>')
def v1_comments(book_id):
    comments = query("SELECT c.comment_id AS id, c.status, COALESCE(NULLIF(c.nickname,''), COALESCE(u.username,'豆瓣书友')) AS user_name, c.content, c.likes, COALESCE(c.comment_date, CAST(c.created_at AS CHAR)) AS created_at, CASE WHEN c.nickname IS NOT NULL AND c.nickname!='' THEN '' ELSE COALESCE(u.avatar_url,'') END AS user_avatar FROM comment c LEFT JOIN user u ON c.user_id=u.user_id WHERE c.book_id=%s AND c.status IN ('normal','pinned') ORDER BY CASE WHEN c.status='pinned' THEN 0 ELSE 1 END, c.likes DESC LIMIT 20", (book_id,))
    return ok({'items': list(comments)})

@app.route('/api/v1/comments', methods=['POST'])
def v1_comment_create():
    u = get_user()
    if not u: return err('请登录', 401)
    d = request.get_json()
    cid = execute("INSERT INTO comment (user_id, book_id, content, status, created_at) VALUES (%s,%s,%s,'normal',NOW())", (u['user_id'], d['book_id'], d['content'][:5000]))
    return ok({
        'id': cid,
        'user_name': u['username'],
        'user_avatar': u.get('avatar_url') or '',
        'content': d['content'][:5000],
        'likes': 0,
        'created_at': '刚刚',
    })

@app.route('/api/v1/comments/<int:comment_id>/like', methods=['POST'])
def v1_comment_like(comment_id):
    execute("UPDATE comment SET likes=likes+1 WHERE comment_id=%s", (comment_id,))
    return ok()

# ═══════ V1 Chat API (DeepSeek RAG) ═══════

import requests as http_requests

def linkify_books(text):
    """将 AI 回复中的《书名》替换为可点击链接，删除所有格式残留"""
    import re
    # 1. 删除所有 (book:x) / （book:x）残留（全角/半角括号、冒号通杀）
    text = re.sub(r'[（(]book[:：]\d+[）)]', '', text)
    # 2. 删除所有 【】 [] 字符
    text = re.sub(r'[【】\[\]]', '', text)
    # 3. 匹配《书名》生成链接
    pattern = re.compile(r'《(.+?)》')
    seen = set()

    def replacer(m):
        title = m.group(1).strip()
        if not title or title in seen: return m.group(0)
        seen.add(title)
        b = query("SELECT book_id FROM book WHERE title=%s AND status=1 LIMIT 1", (title,), one=True)
        if b:
            return f'[《{title}》](book:{b["book_id"]})'
        b2 = query("SELECT book_id FROM book WHERE title LIKE %s AND status=1 LIMIT 1", (f'%{title}%',), one=True)
        if b2:
            return f'[《{title}》](book:{b2["book_id"]})'
        return m.group(0)

    return pattern.sub(replacer, text)

def call_deepseek(messages, stream=False):
    """调用 DeepSeek API，带重试（503/429/超时自动重试最多3次）"""
    api_key = os.getenv('DEEPSEEK_API_KEY', '')
    api_base = os.getenv('DEEPSEEK_API_BASE', 'https://api.deepseek.com/v1')
    last_err = None
    for attempt in range(3):
        try:
            resp = http_requests.post(
                f'{api_base}/chat/completions',
                headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
                json={'model': 'deepseek-chat', 'messages': messages, 'temperature': 0.7, 'max_tokens': 1200},
                timeout=45
            )
            if resp.status_code == 200:
                content = resp.json()['choices'][0]['message']['content']
                # 兼容：新版模型可能返回 JSON 格式 {"reply": "..."}
                if isinstance(content, str) and content.strip().startswith('{'):
                    try:
                        parsed = json.loads(content)
                        if isinstance(parsed, dict) and 'reply' in parsed:
                            return parsed['reply']
                    except (json.JSONDecodeError, TypeError):
                        pass
                return content
            # 503/429 可重试，其他状态码直接抛错
            if resp.status_code in (429, 503):
                last_err = f'DeepSeek {resp.status_code} (attempt {attempt+1}/3)'
                if attempt < 2:
                    wait = (attempt + 1) * 2  # 2s, 4s, 6s
                    import time as _time
                    _time.sleep(wait)
                    continue
            raise Exception(f'DeepSeek API error: {resp.status_code} {resp.text[:200]}')
        except (http_requests.exceptions.Timeout, http_requests.exceptions.ConnectionError) as e:
            last_err = f'Network error (attempt {attempt+1}/3): {str(e)[:80]}'
            if attempt < 2:
                import time as _time
                _time.sleep((attempt + 1) * 2)
                continue
            raise Exception(last_err)
    raise Exception(last_err or 'DeepSeek API failed after 3 retries')

def build_rag_context(book_id=None, user_id=None):
    """构建 RAG 上下文：图书信息 + 知识图谱关联 + 用户画像"""
    ctx_parts = []

    # 当前图书详情
    if book_id:
        b = query("""SELECT b.*, a.name AS author, p.name AS publisher FROM book b
            LEFT JOIN book_author ba ON b.book_id=ba.book_id AND ba.sort_order=0
            LEFT JOIN author a ON ba.author_id=a.author_id
            LEFT JOIN publisher p ON b.publisher_id=p.publisher_id
            WHERE b.book_id=%s""", (book_id,), one=True)
        if b:
            tags = query("SELECT t.name FROM book_tag bt JOIN tag t ON bt.tag_id=t.tag_id WHERE bt.book_id=%s", (book_id,))
            tag_names = [t['name'] for t in tags]
            authors = query("SELECT a.name FROM book_author ba JOIN author a ON ba.author_id=a.author_id WHERE ba.book_id=%s", (book_id,))
            author_names = [a['name'] for a in authors]
            desc = (b.get('description') or '')[:300]
            ctx_parts.append(
                '【当前图书】《' + b['title'] + '》\n' +
                '作者: ' + ', '.join(author_names) + '\n' +
                '出版社: ' + (b.get('publisher') or '未知') + '\n' +
                '评分: ' + str(b.get('score', 0)) + '/10\n' +
                '标签: ' + ', '.join(tag_names) + '\n' +
                '简介: ' + desc
            )

            # 同作者其他书
            if author_names:
                similar = query("""SELECT b2.title, b2.score FROM book b2
                    JOIN book_author ba2 ON b2.book_id=ba2.book_id
                    JOIN author a2 ON ba2.author_id=a2.author_id
                    WHERE a2.name IN ({}) AND b2.book_id != %s
                    GROUP BY b2.book_id ORDER BY b2.score DESC LIMIT 5
                """.format(','.join(['%s']*len(author_names))), author_names + [book_id])
                if similar:
                    books_str = ', '.join('《%s》(%s分)' % (s['title'], s['score']) for s in similar)
                    ctx_parts.append('【同作者其他作品】' + books_str)

            # 同标签热门书
            if tag_names:
                similar2 = query("""SELECT b2.title, b2.score FROM book b2
                    JOIN book_tag bt2 ON b2.book_id=bt2.book_id
                    JOIN tag t2 ON bt2.tag_id=t2.tag_id
                    WHERE t2.name IN ({}) AND b2.book_id != %s
                    GROUP BY b2.book_id ORDER BY b2.score DESC LIMIT 5
                """.format(','.join(['%s']*len(tag_names))), tag_names + [book_id])
                if similar2:
                    books_str2 = ', '.join('《%s》(%s分)' % (s['title'], s['score']) for s in similar2)
                    ctx_parts.append('【同标签热门书】' + books_str2)

    # 用户画像
    if user_id:
        shelf = query("""SELECT b.title, bsi.read_status FROM bookshelf_item bsi
            JOIN bookshelf bs ON bsi.shelf_id=bs.shelf_id
            JOIN book b ON bsi.book_id=b.book_id
            WHERE bs.user_id=%s ORDER BY bsi.added_at DESC LIMIT 10""", (user_id,))
        if shelf:
            status_map = {'want_to_read': '想读', 'reading': '在读', 'finished': '已读'}
            shelf_parts = []
            for s in shelf:
                status_name = status_map.get(s['read_status'], s['read_status'])
                shelf_parts.append('《%s》(%s)' % (s['title'], status_name))
            ctx_parts.append('【用户书架】' + ', '.join(shelf_parts))

    return '\n\n'.join(ctx_parts)

@app.route('/api/v1/chat/send', methods=['POST'])
def v1_chat_send():
    u = get_user()
    if not u: return err('请登录', 401)
    d = request.get_json()
    session_id = d.get('session_id')
    book_id = d.get('book_id')
    user_msg = (d.get('message') or '').strip()
    if not user_msg: return err('请输入消息')

    # 创建或获取会话
    if session_id:
        sess = query("SELECT session_id FROM chat_session WHERE session_id=%s AND user_id=%s", (session_id, u['user_id']), one=True)
        if not sess: session_id = None
    if not session_id:
        title = user_msg[:30].replace('\n', ' ')
        session_id = execute("INSERT INTO chat_session (user_id, title) VALUES (%s, %s)", (u['user_id'], title))

    # 保存用户消息
    execute("INSERT INTO chat_message (session_id, role, content) VALUES (%s, 'user', %s)", (session_id, user_msg))

    # 构建 RAG 上下文 + 历史消息
    context = build_rag_context(book_id, u['user_id'])
    history = query("SELECT role, content FROM chat_message WHERE session_id=%s ORDER BY message_id ASC LIMIT 20", (session_id,))

    # 从数据库获取本站可推荐图书列表
    all_books = query("SELECT title FROM book WHERE status=1 ORDER BY score DESC")
    book_list = '、'.join(f'《{b["title"]}》' for b in all_books)

    system_prompt = (
        '你是一个图书推荐助手，名叫「图图」。\n'
        '关于书籍内容解析、剧情梳理、人物分析、阅读建议等问题，请根据你的知识自由回答。\n'
        '【重要】当用户要求你推荐书籍、列书单、推荐类似作品时，你只能从下方「本站可推荐图书列表」中选择，'
        '不要推荐列表之外的任何书。如果用户想要的类型在列表中找不到完全匹配的，从列表里推荐最接近的即可。\n'
        '请用中文回答，亲切专业，每次回答控制在300字以内。提到书名时仅使用《书名》格式，不要添加任何括号后缀如(book:id)，不要使用【】或[]包裹书名。\n\n'
        '【本站可推荐图书列表】（共' + str(len(all_books)) + '本）：\n' + book_list + '\n\n'
        '【当前上下文】\n' + context
    )

    messages = [{'role': 'system', 'content': system_prompt}]
    for h in history:
        messages.append({'role': h['role'], 'content': h['content']})

    # 调用 DeepSeek
    try:
        reply = call_deepseek(messages)
        reply = linkify_books(reply)  # 为《书名》添加图书链接
    except Exception as e:
        reply = f'抱歉，AI服务暂时不可用，请稍后重试。（{str(e)[:100]}）'

    # 保存 AI 回复（保存的是处理后的带链接版本）
    execute("INSERT INTO chat_message (session_id, role, content) VALUES (%s, 'assistant', %s)", (session_id, reply))

    # 更新会话标题（用第一条用户消息）
    first_msg = query("SELECT content FROM chat_message WHERE session_id=%s AND role='user' ORDER BY message_id ASC LIMIT 1", (session_id,), one=True)
    if first_msg:
        new_title = first_msg['content'][:30].replace('\n', ' ')
        execute("UPDATE chat_session SET title=%s WHERE session_id=%s", (new_title, session_id))

    return ok({
        'session_id': session_id,
        'reply': reply,
        'messages': [{'role': h['role'], 'content': h['content']} for h in history] + [{'role': 'user', 'content': user_msg}, {'role': 'assistant', 'content': reply}]
    })

@app.route('/api/v1/chat/sessions')
def v1_chat_sessions():
    u = get_user()
    if not u: return err('请登录', 401)
    sessions = query("SELECT session_id AS id, title, created_at, updated_at FROM chat_session WHERE user_id=%s ORDER BY updated_at DESC LIMIT 30", (u['user_id'],))
    return ok({'sessions': [{'id': s['id'], 'title': s['title'], 'created_at': str(s['created_at']), 'updated_at': str(s['updated_at'])} for s in sessions]})

@app.route('/api/v1/chat/sessions/<int:session_id>/messages')
def v1_chat_messages(session_id):
    u = get_user()
    if not u: return err('请登录', 401)
    sess = query("SELECT session_id FROM chat_session WHERE session_id=%s AND user_id=%s", (session_id, u['user_id']), one=True)
    if not sess: return err('会话不存在', 404)
    msgs = query("SELECT message_id AS id, role, content, created_at FROM chat_message WHERE session_id=%s ORDER BY message_id ASC", (session_id,))
    return ok({'messages': [{'id': m['id'], 'role': m['role'], 'content': m['content'], 'created_at': str(m['created_at'])} for m in msgs]})

@app.route('/api/v1/chat/sessions/<int:session_id>', methods=['DELETE'])
def v1_chat_delete_session(session_id):
    u = get_user()
    if not u: return err('请登录', 401)
    sess = query("SELECT session_id FROM chat_session WHERE session_id=%s AND user_id=%s", (session_id, u['user_id']), one=True)
    if not sess: return err('会话不存在', 404)
    execute("DELETE FROM chat_message WHERE session_id=%s", (session_id,))
    execute("DELETE FROM chat_session WHERE session_id=%s", (session_id,))
    return ok()

# ═══════ V1 TutuWrite API (DeepSeek 创作) ═══════

TUTUWRITE_SYSTEM = (
    '你是「图图写作」，一个专业的AI文学创作助手。'
    '创作规则：'
    '1. 文体支持：小说、散文、读后感、随笔、议论文、番外、续集、改写剧情、人物小传、书评赏析、应试作文'
    '2. 书籍绑定创作时，严格基于原书设定展开，复刻原作叙事节奏、人物语气、行文风格，续写番外不OOC'
    '3. 输出排版干净：段落间空一行，段首不空格，无多余符号标记，纯文本正文，无markdown，无【】[]书名号装饰'
    '4. 内容合规正向，不生成低俗、暴力、违法内容'
    '5. 书籍衍生类创作在文末标注「*本文为个人同人创作，非官方正版内容」'
    '6. 理解模糊需求时主动推断创作方向，减少无效反问，直接出稿'
    '7. 支持反复迭代：用户要求改写/润色/扩写/精简/改文风时，基于上一版文本修改'
    '8. 字数控制：默认800-1500字；用户指定字数时严格遵循；网文连载支持分章输出'
)

@app.route('/api/v1/tutuWrite/upload-cover', methods=['POST'])
def tutuwrite_upload_cover():
    u = get_user()
    if not u: return err('请登录', 401)
    f = request.files.get('file')
    if not f: return err('请选择文件', 400)
    import uuid, os
    ext = f.filename.rsplit('.', 1)[-1].lower() if '.' in f.filename else 'jpg'
    if ext not in ('jpg','jpeg','png','webp'): return err('仅支持jpg/png/webp', 400)
    name = f'tw_cover_{uuid.uuid4().hex[:8]}.{ext}'
    f.save(os.path.join('static/covers', name))
    return ok({'cover_url': f'/static/covers/{name}'})

@app.route('/api/v1/tutuWrite/send', methods=['POST'])
def tutuwrite_send():
    u = get_user()
    if not u: return err('请登录', 401)
    d = request.get_json()
    session_id = d.get('session_id')
    user_msg = d.get('message', '').strip()
    mode = d.get('mode', 'free')
    book_ids = d.get('book_ids', [])
    action = d.get('action', '')

    if not user_msg: return err('请输入创作需求', 400)

    # 创建或续用会话
    if session_id:
        sess = query("SELECT session_id FROM tutuwrite_session WHERE session_id=%s AND user_id=%s",
                     (session_id, u['user_id']), one=True)
        if not sess: session_id = None
    if not session_id:
        session_id = execute("INSERT INTO tutuwrite_session (user_id, mode) VALUES (%s, %s)", (u['user_id'], mode))

    # 构建书籍上下文
    book_context = ''
    if mode == 'bound' and book_ids:
        ph = ','.join(['%s'] * len(book_ids))
        bound_books = query(f"SELECT book_id, title FROM book WHERE book_id IN ({ph})", book_ids)
        book_context = '【关联书籍】\n' + '\n'.join(f'- 《{b["title"]}》' for b in bound_books) + '\n请基于以上书籍进行创作。\n'

    # 构建 action 提示
    action_hints = {
        'polish': '请润色以下文本，优化措辞但不改变原意和篇幅：',
        'expand': '请扩写以下文本，增加细节描写，扩充篇幅约1.5倍：',
        'condense': '请精简以下文本，压缩冗余保留核心：',
        'restyle': '请改变以下文本的文风：',
        'rewrite': '请基于当前全文重新改写：',
        'partial_rewrite': '请改写以下选中的文本片段：',
    }
    rewrite_target = d.get('rewrite_target', '')
    action_prompt = action_hints.get(action, '')
    if action_prompt and rewrite_target:
        user_msg = action_prompt + '\n' + rewrite_target + '\n用户指令：' + user_msg

    # 历史消息
    history = query("SELECT role, content FROM tutuwrite_message WHERE session_id=%s ORDER BY message_id ASC LIMIT 20", (session_id,))

    # 构建 messages
    messages = [{'role': 'system', 'content': TUTUWRITE_SYSTEM}]
    if book_context:
        messages.append({'role': 'system', 'content': book_context})
    for h in history:
        messages.append({'role': h['role'], 'content': h['content']})
    messages.append({'role': 'user', 'content': user_msg})

    # 保存用户消息
    execute("INSERT INTO tutuwrite_message (session_id, role, content) VALUES (%s, 'user', %s)", (session_id, user_msg))

    # 调用 DeepSeek
    try:
        reply = call_deepseek(messages)
    except Exception as e:
        reply = f'抱歉，AI服务暂时不可用，请稍后重试。（{str(e)[:80]}）'

    execute("INSERT INTO tutuwrite_message (session_id, role, content) VALUES (%s, 'assistant', %s)", (session_id, reply))

    return ok({'session_id': session_id, 'reply': reply})

@app.route('/api/v1/tutuWrite/draft/<int:session_id>', methods=['GET', 'PUT'])
def tutuwrite_draft(session_id):
    u = get_user()
    if not u: return err('请登录', 401)
    sess = query("SELECT session_id FROM tutuwrite_session WHERE session_id=%s AND user_id=%s", (session_id, u['user_id']), one=True)
    if not sess: return err('会话不存在', 404)
    if request.method == 'GET':
        draft = query("SELECT content FROM tutuwrite_draft WHERE session_id=%s", (session_id,), one=True)
        return ok({'content': draft['content'] if draft else ''})
    else:
        d = request.get_json()
        content = d.get('content', '')
        execute("REPLACE INTO tutuwrite_draft (session_id, content) VALUES (%s, %s)", (session_id, content))
        return ok({'saved': True})

@app.route('/api/v1/tutuWrite/sessions')
def tutuwrite_sessions():
    u = get_user()
    if not u: return err('请登录', 401)
    sessions = query("SELECT session_id AS id, mode, title, created_at FROM tutuwrite_session WHERE user_id=%s ORDER BY created_at DESC LIMIT 20", (u['user_id'],))
    return ok({'sessions': [{'id': s['id'], 'mode': s['mode'], 'title': s['title'] or '未命名', 'created_at': str(s['created_at'])} for s in sessions]})

@app.route('/api/v1/tutuWrite/sessions/<int:session_id>/messages')
def tutuwrite_messages(session_id):
    u = get_user()
    if not u: return err('请登录', 401)
    sess = query("SELECT session_id FROM tutuwrite_session WHERE session_id=%s AND user_id=%s", (session_id, u['user_id']), one=True)
    if not sess: return err('会话不存在', 404)
    msgs = query("SELECT message_id AS id, role, content FROM tutuwrite_message WHERE session_id=%s ORDER BY message_id ASC", (session_id,))
    return ok({'messages': [{'id': m['id'], 'role': m['role'], 'content': m['content']} for m in msgs]})

@app.route('/api/v1/tutuWrite/sessions/<int:session_id>', methods=['PUT', 'DELETE'])
def tutuwrite_session(session_id):
    u = get_user()
    if not u: return err('请登录', 401)
    sess = query("SELECT session_id FROM tutuwrite_session WHERE session_id=%s AND user_id=%s", (session_id, u['user_id']), one=True)
    if not sess: return err('会话不存在', 404)
    if request.method == 'PUT':
        d = request.get_json()
        title = d.get('title', '').strip()
        if title:
            execute("UPDATE tutuwrite_session SET title=%s WHERE session_id=%s", (title, session_id))
        return ok({'updated': True})
    else:
        execute("DELETE FROM tutuwrite_message WHERE session_id=%s", (session_id,))
        execute("DELETE FROM tutuwrite_draft WHERE session_id=%s", (session_id,))
        execute("DELETE FROM tutuwrite_session WHERE session_id=%s", (session_id,))
        return ok({'deleted': True})

@app.route('/api/v1/tutuWrite/save', methods=['POST'])
def tutuwrite_save():
    u = get_user()
    if not u: return err('请登录', 401)
    d = request.get_json()
    session_id = d.get('session_id')
    title = d.get('title', '').strip()
    cover_url = d.get('cover_url', '')
    shelf_name = d.get('shelf_name', '我的创作')

    if not title: return err('请输入书名', 400)

    # 获取最后一条 AI 回复作为内容
    content_row = query("SELECT content FROM tutuwrite_message WHERE session_id=%s AND role='assistant' ORDER BY message_id DESC LIMIT 1", (session_id,), one=True)
    content = content_row['content'] if content_row else ''

    # 找或创建书架
    sid = query("SELECT shelf_id FROM bookshelf WHERE user_id=%s AND name=%s", (u['user_id'], shelf_name), one=True)
    if not sid:
        sid = {'shelf_id': execute("INSERT INTO bookshelf (user_id, name, sort_order) VALUES (%s,%s,1)", (u['user_id'], shelf_name))}

    # 不需要实际创建book记录（简化为仅书架记录）
    # 实际项目中这里应该 insert into book 然后 insert into bookshelf_item

    execute("UPDATE tutuwrite_session SET title=%s WHERE session_id=%s", (title, session_id))
    return ok({'saved': True, 'title': title})

# ── 草稿箱 CRUD ──

@app.route('/api/v1/tutuWrite/draft-box', methods=['GET', 'POST'])
def tutuwrite_draft_box():
    u = get_user()
    if not u: return err('请登录', 401)

    if request.method == 'GET':
        drafts = query(
            "SELECT draft_id AS id, book_id, title, content, created_at, updated_at "
            "FROM draft_box WHERE user_id=%s ORDER BY updated_at DESC LIMIT 50",
            (u['user_id'],))
        return ok({'drafts': [{
            'id': d['id'], 'book_id': d.get('book_id'),
            'title': d['title'], 'content': d['content'] or '',
            'created_at': str(d['created_at']), 'updated_at': str(d['updated_at'])
        } for d in drafts]})

    # POST — 新建草稿
    d = request.get_json()
    title = (d.get('title') or '').strip() or '未命名草稿'
    content = d.get('content', '')
    draft_id = execute(
        "INSERT INTO draft_box (user_id, title, content) VALUES (%s, %s, %s)",
        (u['user_id'], title, content))
    return ok({'draft_id': draft_id})


@app.route('/api/v1/tutuWrite/draft-box/<int:draft_id>', methods=['GET', 'PUT', 'DELETE'])
def tutuwrite_draft_box_item(draft_id):
    u = get_user()
    if not u: return err('请登录', 401)
    draft = query(
        "SELECT draft_id, book_id, title, content FROM draft_box "
        "WHERE draft_id=%s AND user_id=%s", (draft_id, u['user_id']), one=True)
    if not draft: return err('草稿不存在', 404)

    if request.method == 'GET':
        return ok({'id': draft['draft_id'], 'book_id': draft.get('book_id'),
                   'title': draft['title'], 'content': draft['content'] or ''})
    if request.method == 'PUT':
        d = request.get_json()
        if d.get('title') is not None:
            execute("UPDATE draft_box SET title=%s WHERE draft_id=%s",
                    (d['title'].strip() or '未命名草稿', draft_id))
        if d.get('content') is not None:
            execute("UPDATE draft_box SET content=%s WHERE draft_id=%s",
                    (d['content'], draft_id))
        return ok({'updated': True})
    # DELETE
    execute("DELETE FROM draft_box WHERE draft_id=%s AND user_id=%s",
            (draft_id, u['user_id']))
    return ok({'deleted': True})


# ── 保存/更新到书架 ──

@app.route('/api/v1/tutuWrite/save-to-shelf', methods=['POST'])
def tutuwrite_save_to_shelf():
    u = get_user()
    if not u: return err('请登录', 401)
    d = request.get_json()
    title = (d.get('title') or '').strip()
    content = (d.get('content') or '').strip()
    cover_url = (d.get('cover_url') or '').strip()
    shelf_name = (d.get('shelf_name') or '').strip() or '我的创作'
    tag_ids = d.get('tag_ids', [])
    draft_id = d.get('draft_id')
    existing_book_id = d.get('book_id')

    if not title: return err('请输入书名', 400)
    if not content: return err('内容不能为空', 400)

    if existing_book_id:
        # ── 更新模式 ──
        book = query("SELECT book_id FROM book WHERE book_id=%s AND description LIKE %s",
                      (existing_book_id, '%用户创作%'), one=True)
        if not book: return err('该书不存在或不是用户创作内容', 404)
        book_id = existing_book_id
        execute("UPDATE book SET title=%s, description=%s, cover_url=%s WHERE book_id=%s",
                (title, '用户创作：' + content[:200], cover_url, book_id))
        # 更新章节
        ch = query("SELECT chapter_id FROM book_chapter WHERE book_id=%s AND chapter_order=0",
                   (book_id,), one=True)
        if ch:
            execute("UPDATE book_chapter SET chapter_name=%s, content=%s, word_count=%s "
                    "WHERE chapter_id=%s",
                    (title, content, len(content), ch['chapter_id']))
        else:
            execute("INSERT INTO book_chapter (book_id, kepub_book_no, chapter_no, "
                    "chapter_name, chapter_order, content, word_count) "
                    "VALUES (%s,%s,%s,%s,0,%s,%s)",
                    (book_id, book_id, 1, title, content, len(content)))
        # 更新标签
        execute("DELETE FROM book_tag WHERE book_id=%s", (book_id,))
        for tid in tag_ids:
            execute("INSERT IGNORE INTO book_tag (book_id, tag_id) VALUES (%s,%s)", (book_id, int(tid)))
    else:
        # ── 创建模式 ──
        book_id = execute("INSERT INTO book (title, description, cover_url, status) "
                          "VALUES (%s,%s,%s,1)",
                          (title, '用户创作：' + content[:200], cover_url))
        execute("INSERT INTO book_chapter (book_id, kepub_book_no, chapter_no, "
                "chapter_name, chapter_order, content, word_count) "
                "VALUES (%s,%s,%s,%s,0,%s,%s)",
                (book_id, book_id, 1, title, content, len(content)))
        if tag_ids:
            for tid in tag_ids:
                execute("INSERT IGNORE INTO book_tag (book_id, tag_id) VALUES (%s,%s)", (book_id, int(tid)))
        # 加入创作书架（仅 writing 类型）
        sid = query("SELECT shelf_id FROM bookshelf WHERE user_id=%s AND name=%s AND shelf_type='writing'",
                    (u['user_id'], shelf_name), one=True)
        if not sid:
            shelf_id = execute("INSERT INTO bookshelf (user_id, name, shelf_type, sort_order) VALUES (%s,%s,'writing',1)",
                              (u['user_id'], shelf_name))
        else:
            shelf_id = sid['shelf_id']
        execute("INSERT INTO bookshelf_item (shelf_id, book_id, read_status) "
                "VALUES (%s,%s,'finished') ON DUPLICATE KEY UPDATE read_status='finished'",
                (shelf_id, book_id))

    if draft_id:
        execute("UPDATE draft_box SET book_id=%s WHERE draft_id=%s AND user_id=%s",
                (book_id, draft_id, u['user_id']))
    return ok({'book_id': book_id, 'shelf_name': shelf_name, 'is_update': bool(existing_book_id)})


# ── 用户创作图书管理 ──

@app.route('/api/v1/tutuWrite/books/<int:book_id>', methods=['PUT'])
def tutuwrite_update_book(book_id):
    """更新用户创作图书的标题、封面"""
    u = get_user()
    if not u: return err('请登录', 401)
    book = query("SELECT book_id FROM book WHERE book_id=%s AND description LIKE %s",
                 (book_id, '%用户创作%'), one=True)
    if not book: return err('该书不存在或不是用户创作内容', 404)
    d = request.get_json()
    if d.get('title') is not None:
        title = d['title'].strip()
        if title:
            execute("UPDATE book SET title=%s WHERE book_id=%s", (title, book_id))
    if d.get('cover_url') is not None:
        execute("UPDATE book SET cover_url=%s WHERE book_id=%s", (d['cover_url'], book_id))
    return ok({'updated': True})


# ═══════ V1 Shelves API ═══════

@app.route('/api/v1/shelves')
def v1_shelves():
    u = get_user()
    if not u: return err('请登录', 401)
    shelf_type_filter = request.args.get('type', '')  # 'reading' or 'writing' or '' for all
    where = "user_id=%s"
    params = [u['user_id']]
    if shelf_type_filter:
        where += " AND shelf_type=%s"
        params.append(shelf_type_filter)
    shelves = query(f"SELECT shelf_id AS id, name, shelf_type, sort_order FROM bookshelf WHERE {where} ORDER BY sort_order", params)
    result = []
    for s in shelves:
        type_map = {'想读': 'want_read', '在读': 'reading', '已读': 'read'}
        s_type = type_map.get(s['name'], s['name'])
        items = query("""
            SELECT bsi.shelf_id AS item_shelf, bsi.shelf_id, b.book_id AS id, b.title, b.cover_url, b.score,
                   b.total_pages, a.name AS author, bsi.read_status, bsi.added_at,
                   rp.current_page, rp.progress_pct AS real_progress
            FROM bookshelf_item bsi
            JOIN book b ON bsi.book_id=b.book_id
            LEFT JOIN book_author ba ON b.book_id=ba.book_id AND ba.sort_order=0
            LEFT JOIN author a ON ba.author_id=a.author_id
            LEFT JOIN reading_progress rp ON rp.book_id=b.book_id AND rp.user_id=%s
            WHERE bsi.shelf_id=%s
        """, (u['user_id'], s['id'],))
        items_out = []
        for it in items:
            # 优先用 reading_progress 的真实页码数据
            real_pct = it.get('real_progress')
            if real_pct is not None:
                progress_pct = float(real_pct)
            else:
                progress_pct = 0
                rs = it.get('read_status', '')
                if rs == 'finished': progress_pct = 100
                elif rs == 'reading': progress_pct = 50
            book_data = {
                'id': it['id'], 'title': it['title'],
                'cover': it.get('cover_url', ''),
                'author': it.get('author') or '',
                'rating': float(it['score'] or 0),
                'total_pages': it.get('total_pages') or 0,
            }
            fix_cover(book_data)
            items_out.append({
                'id': s['id'] * 10000 + it['id'],
                'book': book_data,
                'added_at': str(it['added_at']) if it.get('added_at') else '',
                'reading_progress': progress_pct,
                'current_page': it.get('current_page') or 0,
            })
        result.append({
            'id': s['id'], 'name': s['name'], 'type': s_type,
            'count': len(items_out), 'items': items_out,
        })
    # 仅系统书架标注免费/付费标签
    system_shelf_names = {'想读', '在读', '已读'}
    all_book_data = []
    for shelf in result:
        if shelf['name'] in system_shelf_names:
            for item in shelf['items']:
                if item.get('book'): all_book_data.append(item['book'])
    if all_book_data:
        mark_free_books(all_book_data)
    # 自定义书架移除 is_free
    for shelf in result:
        if shelf['name'] not in system_shelf_names:
            for item in shelf['items']:
                if item.get('book'): item['book'].pop('is_free', None)

    # Ensure 3 default types exist
    existing = {r['type'] for r in result}
    defaults = [('want_read', '想读'), ('reading', '在读'), ('read', '已读')]
    for dt, dn in defaults:
        if dt not in existing:
            sid = execute("INSERT INTO bookshelf (user_id, name, sort_order) VALUES (%s,%s,%s)",
                          (u['user_id'], dn, len(result)+1))
            result.append({'id': sid, 'name': dn, 'type': dt, 'count': 0, 'items': []})
    return ok({'shelves': result})

@app.route('/api/v1/shelves', methods=['POST'])
def v1_shelves_create():
    u = get_user()
    if not u: return err('请登录', 401)
    d = request.get_json()
    name = d.get('name', '').strip()
    if not name: return err('名称不能为空')
    shelf_type = d.get('shelf_type', 'reading')
    if shelf_type not in ('reading', 'writing'): shelf_type = 'reading'
    sid = execute("INSERT INTO bookshelf (user_id, name, shelf_type, sort_order) VALUES (%s,%s,%s,%s)",
                  (u['user_id'], name, shelf_type, 99))
    return ok({'id': sid, 'name': name, 'type': name, 'count': 0, 'items': []})

@app.route('/api/v1/shelves/<int:shelf_id>', methods=['PUT'])
def v1_shelves_update(shelf_id):
    u = get_user()
    if not u: return err('请登录', 401)
    d = request.get_json()
    name = d.get('name', '').strip()
    if not name: return err('名称不能为空')
    execute("UPDATE bookshelf SET name=%s WHERE shelf_id=%s AND user_id=%s", (name, shelf_id, u['user_id']))
    return ok()

@app.route('/api/v1/shelves/<int:shelf_id>', methods=['DELETE'])
def v1_shelves_delete(shelf_id):
    u = get_user()
    if not u: return err('请登录', 401)
    s = query("SELECT * FROM bookshelf WHERE shelf_id=%s AND user_id=%s", (shelf_id, u['user_id']), one=True)
    if not s: return err('书架不存在', 404)
    if s['name'] in ('想读', '在读', '已读'): return err('系统默认书架不可删除')
    execute("DELETE FROM bookshelf WHERE shelf_id=%s AND user_id=%s", (shelf_id, u['user_id']))
    return ok({'id': shelf_id})

@app.route('/api/v1/shelves/items', methods=['POST'])
def v1_shelves_items_add():
    u = get_user()
    if not u: return err('请登录', 401)
    d = request.get_json()
    book_id = d.get('book_id')
    shelf_type = d.get('shelf_type', '')  # want_read / reading / read
    type_name_map = {'want_read': '想读', 'reading': '在读', 'read': '已读'}
    shelf_name = type_name_map.get(shelf_type, shelf_type)

    # 检查是否在自定义书架中，禁止移出
    current_shelf = query(
        "SELECT bs.name FROM bookshelf bs JOIN bookshelf_item bsi ON bs.shelf_id=bsi.shelf_id "
        "WHERE bs.user_id=%s AND bsi.book_id=%s", (u['user_id'], book_id), one=True)
    if current_shelf and current_shelf['name'] not in ('想读', '在读', '已读'):
        return err(f'该书在「{current_shelf["name"]}」书架中，无法移动到其他书架', 403)

    # Find or create shelf
    sid = query("SELECT shelf_id FROM bookshelf WHERE user_id=%s AND name=%s", (u['user_id'], shelf_name), one=True)
    if not sid:
        sid_id = execute("INSERT INTO bookshelf (user_id, name, sort_order) VALUES (%s,%s,%s)",
                         (u['user_id'], shelf_name, 1))
    else:
        sid_id = sid['shelf_id']
    # Check if already in any shelf for this user - remove first
    execute("DELETE bsi FROM bookshelf_item bsi JOIN bookshelf bs ON bsi.shelf_id=bs.shelf_id WHERE bs.user_id=%s AND bsi.book_id=%s",
            (u['user_id'], book_id))
    status_map = {'want_read': 'want_to_read', 'reading': 'reading', 'read': 'finished'}
    st = status_map.get(shelf_type, 'want_to_read')
    execute("INSERT INTO bookshelf_item (shelf_id, book_id, read_status) VALUES (%s,%s,%s)",
            (sid_id, book_id, st))
    return ok({'shelf_type': shelf_type, 'shelf_name': shelf_name})

@app.route('/api/v1/shelves/items/<int:item_id>', methods=['PUT'])
def v1_shelves_items_update(item_id):
    u = get_user()
    if not u: return err('请登录', 401)
    d = request.get_json()
    # Decode composite item_id: shelf_id * 10000 + book_id
    src_shelf_id = item_id // 10000
    book_id = item_id % 10000
    progress = d.get('reading_progress')
    shelf_type = d.get('shelf_type')
    if shelf_type:
        # 检查是否在自定义书架中，禁止移出
        current_shelf = query(
            "SELECT bs.name FROM bookshelf bs JOIN bookshelf_item bsi ON bs.shelf_id=bsi.shelf_id "
            "WHERE bs.user_id=%s AND bsi.book_id=%s", (u["user_id"], book_id), one=True)
        if current_shelf and current_shelf["name"] not in ("想读", "在读", "已读"):
            return err('该书在「' + current_shelf['name'] + '」书架中，无法移动到其他书架', 403)

        # Move book to another shelf
        type_name_map = {"want_read": "想读", "reading": "在读", "read": "已读"}
        shelf_name = type_name_map.get(shelf_type, shelf_type)
        sid = query("SELECT shelf_id FROM bookshelf WHERE user_id=%s AND name=%s", (u["user_id"], shelf_name), one=True)
        if not sid:
            sid = {"shelf_id": execute("INSERT INTO bookshelf (user_id, name, sort_order) VALUES (%s,%s,%s)",
                                        (u["user_id"], shelf_name, 1))}
        # Remove from old shelf, add to new shelf
        execute("DELETE bsi FROM bookshelf_item bsi JOIN bookshelf bs ON bsi.shelf_id=bs.shelf_id WHERE bs.user_id=%s AND bsi.book_id=%s",
                (u["user_id"], book_id))
        status_map = {"want_read": "want_to_read", "reading": "reading", "read": "finished"}
        st = status_map.get(shelf_type, "want_to_read")
        execute("INSERT INTO bookshelf_item (shelf_id, book_id, read_status) VALUES (%s,%s,%s)",
                (sid["shelf_id"], book_id, st))
    if progress is not None:
        # 仅系统书架更新阅读状态
        sid = query("SELECT bs.shelf_id, bs.name FROM bookshelf bs "
                    "JOIN bookshelf_item bsi ON bs.shelf_id=bsi.shelf_id "
                    "WHERE bs.user_id=%s AND bsi.book_id=%s", (u["user_id"], book_id), one=True)
        if sid and sid["name"] in ("想读", "在读", "已读"):
            st = "want_to_read"
            if progress >= 100: st = "finished"
            elif progress > 0: st = "reading"
            execute("UPDATE bookshelf_item bsi JOIN bookshelf bs ON bsi.shelf_id=bsi.shelf_id SET bsi.read_status=%s WHERE bs.user_id=%s AND bsi.book_id=%s",
                    (st, u["user_id"], book_id))
    return ok()

@app.route('/api/v1/shelves/items/remove', methods=['POST'])
def v1_shelves_items_remove_by_book():
    u = get_user()
    if not u: return err('请登录', 401)
    d = request.get_json()
    book_id = d.get('book_id')
    execute("DELETE bsi FROM bookshelf_item bsi JOIN bookshelf bs ON bsi.shelf_id=bs.shelf_id WHERE bs.user_id=%s AND bsi.book_id=%s",
            (u['user_id'], book_id))
    return ok({'removed': True})

@app.route('/api/v1/shelves/items/<int:item_id>', methods=['DELETE'])
def v1_shelves_items_remove(item_id):
    u = get_user()
    if not u: return err('请登录', 401)
    # Decode composite item_id: shelf_id * 10000 + book_id
    book_id = item_id % 10000
    execute("DELETE bsi FROM bookshelf_item bsi JOIN bookshelf bs ON bsi.shelf_id=bs.shelf_id WHERE bs.user_id=%s AND bsi.book_id=%s",
            (u['user_id'], book_id))
    return ok()

def clean_graph_name(name):
    """清洗图节点名称（去除国家前缀等）"""
    if not name: return '未知'
    n = str(name)
    n = n.lstrip(':').lstrip('：')
    n = re.sub(r'^\[[^]]+\]\s*', '', n)
    n = re.sub(r'\s+[著等编译注译校]$', '', n)
    return n.strip() or '未知'

# ═══════ 用户端知识图谱探索 API ═══════

@app.route('/api/v1/graph/filter-options')
def graph_filter_options():
    """返回图谱筛选面板可用的标签和作者"""
    tags = query("SELECT tag_id AS id, name FROM tag ORDER BY name")
    authors = query("""
        SELECT a.author_id AS id, a.name, COUNT(ba.book_id) AS book_count
        FROM author a
        JOIN book_author ba ON a.author_id = ba.author_id
        GROUP BY a.author_id, a.name
        ORDER BY book_count DESC LIMIT 100
    """)
    return ok({
        'tags': [{'id': t['id'], 'name': t['name']} for t in tags],
        'authors': [{'id': a['id'], 'name': a['name']} for a in authors],
    })

@app.route('/api/v1/graph/filter')
def graph_filter_result():
    """AND逻辑筛选 + Neo4j图谱生成
    参数: tags(逗号分隔), authors(逗号分隔), price(free/paid), depth(1/2), limit(默认30)
    """
    tag_str = request.args.get('tags', '')
    author_str = request.args.get('authors', '')
    price = request.args.get('price', '')
    depth = int(request.args.get('depth', 1))
    limit = int(request.args.get('limit', 30))
    if depth not in (1, 2): depth = 1

    tag_list = [t.strip() for t in tag_str.split(',') if t.strip()] if tag_str else []
    author_list = [a.strip() for a in author_str.split(',') if a.strip()] if author_str else []

    categories = [
        {'name': '图书', 'itemStyle': {'color': '#D4A24C'}},
        {'name': '作者', 'itemStyle': {'color': '#3498DB'}},
        {'name': '标签', 'itemStyle': {'color': '#2ECC71'}},
    ]

    # ── Step 1: MySQL AND 逻辑筛选 ──
    wheres = ["b.status=1"]
    params = []

    # 标签 AND 筛选
    if tag_list:
        ph = ','.join(['%s'] * len(tag_list))
        tag_sql = f"""b.book_id IN (
            SELECT bt.book_id FROM book_tag bt
            JOIN tag t ON bt.tag_id = t.tag_id
            WHERE t.name IN ({ph})
            GROUP BY bt.book_id
            HAVING COUNT(DISTINCT t.name) = %s
        )"""
        wheres.append(tag_sql)
        params.extend(tag_list)
        params.append(len(tag_list))

    # 作者 AND 筛选（模糊匹配）
    if author_list:
        for a in author_list:
            wheres.append("""b.book_id IN (
                SELECT ba2.book_id FROM book_author ba2
                JOIN author a2 ON ba2.author_id = a2.author_id
                WHERE a2.name LIKE %s
            )""")
            params.append(f"%{a}%")

    # 价格筛选
    FREE_COND = "(b.ebook_url IS NOT NULL AND b.ebook_url != '' OR b.book_id IN (SELECT DISTINCT book_id FROM book_chapter))"
    PAID_COND = "(b.ebook_url IS NULL OR b.ebook_url = '') AND b.book_id NOT IN (SELECT DISTINCT book_id FROM book_chapter)"
    if price == 'free':
        wheres.append(FREE_COND)
    elif price == 'paid':
        wheres.append(PAID_COND)

    where_clause = ' AND '.join(wheres)
    sql = f"SELECT b.book_id, b.douban_id, b.title, COALESCE(b.score,0) AS score FROM book b WHERE {where_clause} ORDER BY b.score DESC LIMIT %s"
    params.append(limit)
    books = query(sql, params)

    total = len(books)
    if total == 0:
        return ok({
            'type': 'filter_result', 'nodes': [], 'links': [], 'categories': categories,
            'node_stats': {'book': 0, 'author': 0, 'tag': 0},
            'total': 0, 'message': '暂无符合条件的图书，请重新选择'
        })

    # ── Step 2: Neo4j 构建图谱 ──
    try:
        from recommendation.config import get_neo4j_cfg
        cfg = get_neo4j_cfg()
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver(cfg['uri'], auth=(cfg['user'], cfg['password']))
        nodes, links, node_ids = [], [], set()

        def add_node(nid, name, category, score=None, mysql_id=None):
            if nid not in node_ids:
                node_ids.add(nid)
                sz = max(20, min(50, (score or 5) * 5)) if category == 'book' else 18
                nd = {'id': nid, 'name': str(name)[:40], 'category': category, 'symbolSize': sz}
                if mysql_id: nd['mysql_id'] = mysql_id
                nodes.append(nd)

        with driver.session(database=cfg.get('database', 'neo4j')) as s:
            for b in books:
                douban_id = str(b['douban_id'])
                seed = 'book_' + douban_id
                add_node(seed, b['title'], 'book', float(b['score'] or 0), mysql_id=b['book_id'])

                # 作者
                for r in s.run("MATCH (b:Book {book_id:$bid})-[:WRITTEN_BY]->(a:Author) RETURN a.name AS n", bid=douban_id):
                    cn = clean_graph_name(r['n'])
                    add_node('author_' + cn, cn, 'author')
                    links.append({'source': seed, 'target': 'author_' + cn, 'label': '作者'})

                # 标签
                for r in s.run("MATCH (b:Book {book_id:$bid})-[:HAS_TAG]->(t:Tag) RETURN t.name AS n", bid=douban_id):
                    cn = clean_graph_name(r['n'])
                    add_node('tag_' + cn, cn, 'tag')
                    links.append({'source': seed, 'target': 'tag_' + cn, 'label': '标签'})

            # Step 3: 二级关联展开
            if depth >= 2:
                book_ids_for_neo = [str(b['douban_id']) for b in books]
                for bid in book_ids_for_neo:
                    ab = list(s.run(
                        "MATCH (b:Book {book_id:$bid})-[:WRITTEN_BY]->(a:Author)<-[:WRITTEN_BY]-(o:Book) "
                        "WHERE o.book_id <> $bid RETURN o.book_id AS oid, o.title AS t, o.score AS s, a.name AS an LIMIT 5",
                        bid=bid))
                    tb = list(s.run(
                        "MATCH (b:Book {book_id:$bid})-[:HAS_TAG]->(t:Tag)<-[:HAS_TAG]-(o:Book) "
                        "WHERE o.book_id <> $bid RETURN o.book_id AS oid, o.title AS t, o.score AS s, t.name AS tn LIMIT 5",
                        bid=bid))
                    # 批量查 mysql_id
                    all_dbs = [str(r['oid']) for r in ab] + [str(r['oid']) for r in tb]
                    d2m = {}
                    if all_dbs:
                        ph = ','.join(['%s'] * len(all_dbs))
                        d2m = {str(r['douban_id']): r['book_id'] for r in query(f"SELECT book_id, douban_id FROM book WHERE douban_id IN ({ph})", all_dbs)}
                    for r in ab:
                        oid = 'book_' + str(r['oid'])
                        add_node(oid, r['t'], 'book', float(r['s'] or 0), mysql_id=d2m.get(str(r['oid'])))
                        add_node('author_' + clean_graph_name(r['an']), clean_graph_name(r['an']), 'author')
                        links.append({'source': oid, 'target': 'author_' + clean_graph_name(r['an']), 'label': '作者'})
                    for r in tb:
                        oid = 'book_' + str(r['oid'])
                        add_node(oid, r['t'], 'book', float(r['s'] or 0), mysql_id=d2m.get(str(r['oid'])))
                        add_node('tag_' + clean_graph_name(r['tn']), clean_graph_name(r['tn']), 'tag')
                        links.append({'source': oid, 'target': 'tag_' + clean_graph_name(r['tn']), 'label': '标签'})

        driver.close()
        return ok({
            'type': 'filter_result', 'nodes': nodes, 'links': links, 'categories': categories,
            'node_stats': {
                'book': sum(1 for n in nodes if n['category'] == 'book'),
                'author': sum(1 for n in nodes if n['category'] == 'author'),
                'tag': sum(1 for n in nodes if n['category'] == 'tag'),
            },
            'total': total, 'message': f'找到 {total} 本满足全部条件的图书'
        })
    except Exception as e:
        print(f"Graph filter error: {e}")
        return ok({
            'type': 'filter_result', 'nodes': [], 'links': [], 'categories': categories,
            'node_stats': {'book': 0, 'author': 0, 'tag': 0},
            'total': 0, 'message': f'图谱生成失败: {str(e)[:80]}'
        })

@app.route('/api/v1/graph/search')
def user_graph_search():
    """参数：keyword, book_id, author, tag, depth（无管理员权限要求，仅3类：图书/作者/标签）"""
    keyword = request.args.get('keyword', '').strip()
    book_id = request.args.get('book_id')
    author_name = request.args.get('author')
    tag_name = request.args.get('tag')
    depth = int(request.args.get('depth', 1))
    if depth not in (1, 2): depth = 1

    categories = [
        {'name': '图书', 'itemStyle': {'color': '#D4A24C'}},
        {'name': '作者', 'itemStyle': {'color': '#3498DB'}},
        {'name': '标签', 'itemStyle': {'color': '#2ECC71'}},
    ]

    # ── 关键词搜索 ──
    if keyword:
        books = query("SELECT book_id, title, score FROM book WHERE title LIKE %s AND status=1 ORDER BY score DESC LIMIT 8",
                      (f'%{keyword}%',))
        authors = query("SELECT author_id, name FROM author WHERE name LIKE %s LIMIT 6", (f'%{keyword}%',))
        tags = query("SELECT tag_id, name FROM tag WHERE name LIKE %s LIMIT 6", (f'%{keyword}%',))
        return ok({
            'type': 'search_results',
            'books': [{'book_id': b['book_id'], 'title': b['title'], 'score': float(b['score'] or 0)} for b in books],
            'authors': [{'author_id': a['author_id'], 'name': a['name']} for a in authors],
            'tags': [{'tag_id': t['tag_id'], 'name': t['name']} for t in tags],
            'categories': categories,
        })

    # ── 无参数 → Top10 高分书籍图谱 ──
    if not book_id and not author_name and not tag_name:
        top_books = query("SELECT book_id, douban_id, title, score FROM book WHERE status=1 ORDER BY score DESC LIMIT 10")
        try:
            from recommendation.config import get_neo4j_cfg
            cfg = get_neo4j_cfg()
            from neo4j import GraphDatabase
            driver = GraphDatabase.driver(cfg['uri'], auth=(cfg['user'], cfg['password']))
            _nodes, _links, _ids = [], [], set()
            def _add(nid, name, cat, score=None, mysql_id=None):
                if nid not in _ids:
                    _ids.add(nid)
                    sz = max(20, min(50, (score or 5) * 5)) if cat == 'book' else 18
                    nd = {'id': nid, 'name': str(name)[:40], 'category': cat, 'symbolSize': sz}
                    if mysql_id: nd['mysql_id'] = mysql_id
                    _nodes.append(nd)
            with driver.session(database=cfg.get('database','neo4j')) as s:
                for b in top_books:
                    douban_id = str(b['douban_id'])
                    seed = 'book_' + douban_id
                    _add(seed, b['title'], 'book', float(b['score'] or 0), mysql_id=b['book_id'])
                    for r in s.run("MATCH (b:Book {book_id:$bid})-[:WRITTEN_BY]->(a:Author) RETURN a.name AS n", bid=douban_id):
                        cn = clean_graph_name(r['n'])
                        _add('author_'+cn, cn, 'author')
                        _links.append({'source': seed, 'target': 'author_'+cn, 'label': '作者'})
                    for r in s.run("MATCH (b:Book {book_id:$bid})-[:HAS_TAG]->(t:Tag) RETURN t.name AS n", bid=douban_id):
                        cn = clean_graph_name(r['n'])
                        _add('tag_'+cn, cn, 'tag')
                        _links.append({'source': seed, 'target': 'tag_'+cn, 'label': '标签'})
            driver.close()
            return ok({
                'type': 'top10_overview', 'nodes': _nodes, 'links': _links,
                'node_stats': {
                    'book': sum(1 for n in _nodes if n['category']=='book'),
                    'author': sum(1 for n in _nodes if n['category']=='author'),
                    'tag': sum(1 for n in _nodes if n['category']=='tag'),
                },
                'categories': categories, 'source': 'neo4j'
            })
        except Exception as e:
            print(f"User graph top10 error: {e}")
            return ok({'type': 'empty', 'categories': categories})

    # ── 自我中心网络 ──
    try:
        from recommendation.config import get_neo4j_cfg
        cfg = get_neo4j_cfg()
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver(cfg['uri'], auth=(cfg['user'], cfg['password']))
        nodes, links, node_ids = [], [], set()
        def add_node(nid, name, category, score=None, mysql_id=None):
            if nid not in node_ids:
                node_ids.add(nid)
                sz = max(20, min(50, (score or 5) * 5)) if category == 'book' else 18
                nd = {'id': nid, 'name': str(name)[:40], 'category': category, 'symbolSize': sz}
                if mysql_id: nd['mysql_id'] = mysql_id
                nodes.append(nd)

        with driver.session(database=cfg.get('database','neo4j')) as s:
            if book_id:
                book_row = query("SELECT book_id, douban_id, title, score FROM book WHERE book_id=%s", (book_id,), one=True)
                if not book_row: driver.close(); return err('图书不存在', 404)
                douban_id = str(book_row['douban_id'])
                seed_id = 'book_' + douban_id
                add_node(seed_id, book_row['title'], 'book', float(book_row['score'] or 0), mysql_id=book_row['book_id'])
                for r in s.run("MATCH (b:Book {book_id:$bid})-[:WRITTEN_BY]->(a:Author) RETURN a.name AS n", bid=douban_id):
                    cn = clean_graph_name(r['n'])
                    add_node('author_'+cn, cn, 'author')
                    links.append({'source': seed_id, 'target': 'author_'+cn, 'label': '作者'})
                for r in s.run("MATCH (b:Book {book_id:$bid})-[:HAS_TAG]->(t:Tag) RETURN t.name AS n", bid=douban_id):
                    cn = clean_graph_name(r['n'])
                    add_node('tag_'+cn, cn, 'tag')
                    links.append({'source': seed_id, 'target': 'tag_'+cn, 'label': '标签'})
                # 二级：同作者/同标签的其他书
                if depth >= 2:
                    author_books = list(s.run("MATCH (b:Book {book_id:$bid})-[:WRITTEN_BY]->(a:Author)<-[:WRITTEN_BY]-(o:Book) WHERE o.book_id<>$bid RETURN o.book_id AS bid, o.title AS t, o.score AS s, a.name AS an", bid=douban_id))
                    tag_books = list(s.run("MATCH (b:Book {book_id:$bid})-[:HAS_TAG]->(t:Tag)<-[:HAS_TAG]-(o:Book) WHERE o.book_id<>$bid RETURN o.book_id AS bid, o.title AS t, o.score AS s, t.name AS tn", bid=douban_id))
                    # 批量查询 douban_id → mysql book_id
                    all_dbs = [str(r['bid']) for r in author_books] + [str(r['bid']) for r in tag_books]
                    d2m = {}
                    if all_dbs:
                        ph = ','.join(['%s'] * len(all_dbs))
                        d2m = {str(r['douban_id']): r['book_id'] for r in query(f"SELECT book_id, douban_id FROM book WHERE douban_id IN ({ph})", all_dbs)}
                    for r in author_books:
                        oid = 'book_' + str(r['bid'])
                        add_node(oid, r['t'], 'book', float(r['s'] or 0), mysql_id=d2m.get(str(r['bid'])))
                        links.append({'source': 'author_'+clean_graph_name(r['an']), 'target': oid, 'label': '作者'})
                    for r in tag_books:
                        oid = 'book_' + str(r['bid'])
                        add_node(oid, r['t'], 'book', float(r['s'] or 0), mysql_id=d2m.get(str(r['bid'])))
                        links.append({'source': 'tag_'+clean_graph_name(r['tn']), 'target': oid, 'label': '标签'})

            elif author_name:
                cn = clean_graph_name(author_name)
                aid = 'author_' + cn
                add_node(aid, cn, 'author')
                # 批量查询 douban_id → mysql book_id 映射
                neo_books = s.run("MATCH (a:Author)<-[:WRITTEN_BY]-(b:Book) WHERE a.name CONTAINS $n RETURN b.book_id AS bid, b.title AS t, b.score AS s LIMIT 50", n=author_name)
                neo_list = [(r['bid'], r['t'], float(r['s'] or 0)) for r in neo_books]
                douban_to_mysql = {}
                if neo_list:
                    douban_ids = [str(bid) for bid, _, _ in neo_list]
                    ph = ','.join(['%s'] * len(douban_ids))
                    mysql_rows = query(f"SELECT book_id, douban_id FROM book WHERE douban_id IN ({ph})", douban_ids)
                    douban_to_mysql = {str(r['douban_id']): r['book_id'] for r in mysql_rows}
                for bid, t, s in neo_list:
                    oid = 'book_' + str(bid)
                    add_node(oid, t, 'book', s, mysql_id=douban_to_mysql.get(str(bid)))
                    links.append({'source': oid, 'target': aid, 'label': '作者'})
                    if depth >= 2:
                        for tr in s.run("MATCH (b:Book {book_id:$bid})-[:HAS_TAG]->(t:Tag) RETURN t.name AS n", bid=str(bid)):
                            ct = clean_graph_name(tr['n'])
                            add_node('tag_' + ct, ct, 'tag')
                            links.append({'source': oid, 'target': 'tag_' + ct, 'label': '标签'})

            elif tag_name:
                cn = clean_graph_name(tag_name)
                tid = 'tag_' + cn
                add_node(tid, cn, 'tag')
                neo_books = s.run("MATCH (t:Tag)<-[:HAS_TAG]-(b:Book) WHERE t.name CONTAINS $n RETURN b.book_id AS bid, b.title AS t, b.score AS s LIMIT 50", n=tag_name)
                neo_list = [(r['bid'], r['t'], float(r['s'] or 0)) for r in neo_books]
                douban_to_mysql = {}
                if neo_list:
                    douban_ids = [str(bid) for bid, _, _ in neo_list]
                    ph = ','.join(['%s'] * len(douban_ids))
                    mysql_rows = query(f"SELECT book_id, douban_id FROM book WHERE douban_id IN ({ph})", douban_ids)
                    douban_to_mysql = {str(r['douban_id']): r['book_id'] for r in mysql_rows}
                for bid, t, s in neo_list:
                    oid = 'book_' + str(bid)
                    add_node(oid, t, 'book', s, mysql_id=douban_to_mysql.get(str(bid)))
                    links.append({'source': oid, 'target': tid, 'label': '标签'})
                    if depth >= 2:
                        for ar in s.run("MATCH (b:Book {book_id:$bid})-[:WRITTEN_BY]->(a:Author) RETURN a.name AS n", bid=str(bid)):
                            ca = clean_graph_name(ar['n'])
                            add_node('author_' + ca, ca, 'author')
                            links.append({'source': oid, 'target': 'author_' + ca, 'label': '作者'})
        driver.close()
        return ok({'type': 'ego_network', 'nodes': nodes, 'links': links, 'categories': categories})
    except Exception as e:
        print(f"User graph error: {e}")
        return ok({'type': 'error', 'message': str(e), 'categories': categories})

# ═══════ V1 API END ═══════

@app.route('/api/v1/proxy/image')
def proxy_image():
    """代理豆瓣图片，绕过防盗链"""
    url = request.args.get('url', '')
    if not url: return '', 400
    import requests as req
    try:
        h = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://book.douban.com/subject/',
            'Accept': 'image/avif,image/webp,image/apng,image/*,*/*;q=0.8',
        }
        r = req.get(url, headers=h, timeout=10)
        from flask import Response
        return Response(r.content, mimetype=r.headers.get('Content-Type', 'image/jpeg'))
    except:
        return '', 404

def rating_stars_html(book_id, user_rating):
    """生成五星评分HTML"""
    stars = ''
    for i in range(1, 6):
        active = user_rating and user_rating >= i
        stars += f'<span onclick="rateBook({book_id},{i})" style="cursor:pointer;font-size:22px;color:{"#e67e22" if active else "#ddd"}">★</span>'
    return f'<div class="flex-row" style="margin-top:8px"><span>我的评分：</span>{stars}</div>'

def page(title, body, user=None):
    tpl = f'<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title}</title>{CSS}</head><body>{NAV}{body}{FOOT}'
    return render_template_string(tpl, user=user)

# ═══════════ Auth ═══════════

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username','').strip()
    password = request.form.get('password','').strip()
    email = request.form.get('email','').strip()
    if not username or len(password) < 4:
        return '<script>alert("用户名不能空，密码至少4位");history.back()</script>'
    if query("SELECT user_id FROM user WHERE username=%s", (username,), one=True):
        return '<script>alert("用户名已存在");history.back()</script>'
    h = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    execute("INSERT INTO user (username, password_hash, email, role) VALUES (%s,%s,%s,'reader')", (username, h, email))
    return '<script>alert("注册成功！");location.href="/login"</script>'

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username','').strip()
    password = request.form.get('password','').strip()
    u = query("SELECT * FROM user WHERE username=%s", (username,), one=True)
    if u and bcrypt.checkpw(password.encode(), u['password_hash'].encode()):
        session['user_id'] = u['user_id']
        return redirect('/')
    return '<script>alert("用户名或密码错误");history.back()</script>'

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/login')
def login_page():
    return page('登录', '''
    <div class="form-card"><h2>登录</h2><form method="POST" action="/login">
    <input name="username" placeholder="用户名" required><input name="password" type="password" placeholder="密码" required>
    <button type="submit" class="btn btn-primary" style="width:100%;margin-top:12px">登录</button></form>
    <p style="margin-top:12px;text-align:center">没有账号？<a href="/register">注册</a></p></div>''')

@app.route('/register')
def register_page():
    return page('注册', '''
    <div class="form-card"><h2>注册</h2><form method="POST" action="/register">
    <input name="username" placeholder="用户名" required>
    <input name="password" type="password" placeholder="密码(至少4位)" required>
    <button type="submit" class="btn btn-primary" style="width:100%;margin-top:12px">注册</button></form>
    <p style="margin-top:12px;text-align:center">已有账号？<a href="/login">登录</a></p></div>''')

# ═══════════ Shelf API ═══════════

@app.route('/api/shelf/add', methods=['POST'])
@login_required
def shelf_add():
    u = get_user()
    d = request.get_json()
    sid = query("SELECT shelf_id FROM bookshelf WHERE user_id=%s AND name='默认书架'", (u['user_id'],), one=True)
    if not sid: sid = {'shelf_id': execute("INSERT INTO bookshelf (user_id,name,sort_order) VALUES (%s,'默认书架',1)", (u['user_id'],))}
    execute("REPLACE INTO bookshelf_item (shelf_id,book_id,read_status) VALUES (%s,%s,%s)",
            (sid['shelf_id'], d['book_id'], d.get('status','want_to_read')))
    return jsonify({'ok': True})

@app.route('/api/shelf/remove', methods=['POST'])
@login_required
def shelf_remove():
    u = get_user()
    d = request.get_json()
    execute("DELETE bsi FROM bookshelf_item bsi JOIN bookshelf bs ON bsi.shelf_id=bs.shelf_id WHERE bs.user_id=%s AND bsi.book_id=%s",
            (u['user_id'], d['book_id']))
    return jsonify({'ok': True})

# ═══════════ Comment API ═══════════

@app.route('/api/comment/post', methods=['POST'])
@login_required
def comment_post():
    u = get_user()
    d = request.get_json()
    content = d.get('content','').strip()
    if not content: return jsonify({'ok': False})
    execute("INSERT INTO comment (user_id,book_id,content,status) VALUES (%s,%s,%s,'normal')",
            (u['user_id'], d['book_id'], content[:5000]))
    return jsonify({'ok': True})

@app.route('/api/comment/like', methods=['POST'])
@login_required
def comment_like():
    d = request.get_json()
    execute("UPDATE comment SET likes=likes+1 WHERE comment_id=%s", (d['comment_id'],))
    return jsonify({'ok': True})

# ═══════════ Rec Feedback ═══════════

@app.route('/api/rec/feedback', methods=['POST'])
@login_required
def rec_feedback():
    u = get_user()
    d = request.get_json()
    execute("INSERT INTO user_behavior (user_id, action_type, target_id, created_at) VALUES (%s,%s,%s,NOW())",
            (u['user_id'], d['action'], d['book_id']))
    return jsonify({'ok': True})

# ═══════════ Rating ═══════════

@app.route('/api/rate', methods=['POST'])
@login_required
def rate_book():
    u = get_user()
    d = request.get_json()
    execute("REPLACE INTO rating (user_id, book_id, score, created_at) VALUES (%s,%s,%s,NOW())",
            (u['user_id'], d['book_id'], d['score']))
    return jsonify({'ok': True})

# ═══════════ Purchase Links (seed demo) ═══════════

@app.route('/api/purchase/<int:book_id>')
def get_purchase_links(book_id):
    links = query("SELECT platform, url, price FROM purchase_link WHERE book_id=%s ORDER BY price", (book_id,))
    return jsonify(list(links))

# ═══════════ Admin ═══════════

def admin_required(f):
    @wraps(f)
    def wrap(*a, **kw):
        u = get_user()
        if not u or u['role'] != 'admin': return redirect('/login')
        return f(*a, **kw)
    return wrap

@app.route('/admin')
@admin_required
def admin_page():
    u = get_user()
    comments = query("SELECT c.*, b.title AS book_title, u2.username FROM comment c JOIN book b ON c.book_id=b.book_id JOIN user u2 ON c.user_id=u2.user_id ORDER BY c.created_at DESC LIMIT 50")

    body = '<h2>⚙️ 管理后台</h2>'
    body += '<div class="section-title">📝 评论管理</div>'
    for c in comments:
        status = c['status']
        body += f'''<div class="card" style="margin-bottom:6px">
        <div class="meta">[{c["book_title"]}] {c["username"]} · {c.get("display_date","")} · ❤️{c["likes"]} · <span class="badge">{status}</span></div>
        <p style="margin:4px 0">{c["content"][:200]}</p>
        <div class="flex-row">'''
        if status == 'normal':
            body += f'<button class="btn btn-sm btn-outline" onclick="modComment({c["comment_id"]},\'pinned\')">📌 置顶</button>'
        body += f'<button class="btn btn-sm btn-danger" onclick="modComment({c["comment_id"]},\'deleted\')">🗑 删除</button></div></div>'
    body += '<script>async function modComment(cid,st){await fetch("/api/admin/comment",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({comment_id:cid,status:st})});location.reload()}</script>'
    return page('管理后台', body, u)

@app.route('/api/admin/comment', methods=['POST'])
@admin_required
def admin_comment():
    d = request.get_json()
    execute("UPDATE comment SET status=%s WHERE comment_id=%s", (d['status'], d['comment_id']))
    return jsonify({'ok': True})

@app.route('/api/admin/purchase', methods=['POST'])
@admin_required
def admin_purchase():
    d = request.get_json()
    execute("INSERT INTO purchase_link (book_id, platform, url, price) VALUES (%s,%s,%s,%s) ON DUPLICATE KEY UPDATE url=VALUES(url), price=VALUES(price)",
            (d['book_id'], d['platform'], d['url'], d.get('price')))
    return jsonify({'ok': True})

# ═══════════ Admin V1 API (MySQL) ═══════════

def admin_required_v1(f):
    @wraps(f)
    def wrap(*a, **kw):
        u = get_user()
        if not u or u['role'] != 'admin':
            return err('需要管理员权限', 403)
        return f(*a, **kw)
    return wrap

@app.route('/api/v1/admin/login', methods=['POST'])
def admin_login():
    """管理员登录：先验证用户名密码，再检查是否为 admin 角色"""
    d = request.get_json()
    u = query("SELECT * FROM user WHERE username=%s", (d.get('username', ''),), one=True)
    if not u or not bcrypt.checkpw(d.get('password', '').encode(), u['password_hash'].encode()):
        return err('用户名或密码错误', 401)
    if u['role'] != 'admin':
        return err('非管理员账号，无法登录后台', 403)
    session['user_id'] = u['user_id']
    token = create_access_token(u['user_id'])
    execute("INSERT INTO user_behavior (user_id,action_type,target_type,target_id,created_at) VALUES (%s,'login','book',0,NOW())", (u['user_id'],))
    return ok({
        'access_token': token, 'token_type': 'bearer',
        'user': {'id': u['user_id'], 'username': u['username'], 'role': u['role']}
    })

# ── Books CRUD ──

@app.route('/api/v1/admin/books/upload-cover', methods=['POST'])
@admin_required_v1
def admin_upload_cover():
    file = request.files.get('file')
    if not file or file.filename == '':
        return err('请选择图片文件')
    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    if ext not in ALLOWED_AVATAR_EXTS:
        return err('仅支持 png, jpg, jpeg, gif, webp 格式')
    import uuid
    filename = f"cover_{uuid.uuid4().hex[:8]}.{ext}"
    filepath = os.path.join('static', 'covers', filename)
    file.save(filepath)
    cover_url = f'/static/covers/{filename}'
    return ok({'cover_url': cover_url})

@app.route('/api/v1/admin/books')
@admin_required_v1
def admin_books():
    page = int(request.args.get('page', 1))
    size = int(request.args.get('size', 20))
    keyword = request.args.get('keyword', '')
    off = (page - 1) * size
    if keyword:
        books = query("""
            SELECT b.*, a.name AS author, p.name AS publisher
            FROM book b
            LEFT JOIN book_author ba ON b.book_id=ba.book_id AND ba.sort_order=0
            LEFT JOIN author a ON ba.author_id=a.author_id
            LEFT JOIN publisher p ON b.publisher_id=p.publisher_id
            WHERE b.title LIKE %s
            ORDER BY b.book_id DESC LIMIT %s OFFSET %s
        """, (f"%{keyword}%", size, off))
        total = query("SELECT COUNT(*) AS n FROM book WHERE title LIKE %s", (f"%{keyword}%",), one=True)['n']
    else:
        books = query("""
            SELECT b.*, a.name AS author, p.name AS publisher
            FROM book b
            LEFT JOIN book_author ba ON b.book_id=ba.book_id AND ba.sort_order=0
            LEFT JOIN author a ON ba.author_id=a.author_id
            LEFT JOIN publisher p ON b.publisher_id=p.publisher_id
            ORDER BY b.book_id DESC LIMIT %s OFFSET %s
        """, (size, off))
        total = query("SELECT COUNT(*) AS n FROM book", one=True)['n']
    items = []
    for b in books:
        tags = query("SELECT t.name FROM book_tag bt JOIN tag t ON bt.tag_id=t.tag_id WHERE bt.book_id=%s", (b['book_id'],))
        items.append({
            'id': b['book_id'], 'title': b['title'], 'isbn': b.get('isbn'), 'score': b.get('score'),
            'cover': b.get('cover_url'), 'publisher': b.get('publisher'), 'author': b.get('author'),
            'publish_year': b.get('publish_year'), 'total_pages': b.get('total_pages'),
            'description': b.get('description'), 'status': b.get('status'),
            'tags': [t['name'] for t in tags],
            'created_at': str(b.get('created_at', '')),
        })
    return ok({'items': items, 'total': total, 'page': page, 'size': size})

@app.route('/api/v1/admin/books', methods=['POST'])
@admin_required_v1
def admin_create_book():
    d = request.get_json()
    # 处理 publisher: 接受名称字符串，自动查找或创建
    pub_name = (d.get('publisher') or '').strip()
    pub_id = None
    if pub_name:
        pub = query("SELECT publisher_id FROM publisher WHERE name=%s", (pub_name,), one=True)
        if pub:
            pub_id = pub['publisher_id']
        else:
            pub_id = execute("INSERT INTO publisher (name) VALUES (%s)", (pub_name,))
    bid = execute("""INSERT INTO book (title, isbn, description, cover_url, publisher_id, total_pages, publish_year, score, status)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,1)""",
        (d['title'], d.get('isbn'), d.get('description'), d.get('cover'),
         pub_id, d.get('total_pages'), d.get('publish_year'), d.get('score', 0)))
    # 处理 author: 多个用 / 分隔
    author_str = (d.get('author') or '').strip()
    if author_str:
        for name in author_str.split('/'):
            name = name.strip()
            if not name: continue
            a = query("SELECT author_id FROM author WHERE name=%s", (name,), one=True)
            if a:
                aid = a['author_id']
            else:
                aid = execute("INSERT INTO author (name) VALUES (%s)", (name,))
            execute("INSERT INTO book_author (book_id, author_id, sort_order) VALUES (%s,%s,%s) ON DUPLICATE KEY UPDATE author_id=author_id",
                    (bid, aid, 0))
    return ok({'id': bid})

@app.route('/api/v1/admin/books/<int:book_id>', methods=['PUT'])
@admin_required_v1
def admin_update_book(book_id):
    d = request.get_json()
    pub_name = (d.get('publisher') or '').strip()
    pub_id = None
    if pub_name:
        pub = query("SELECT publisher_id FROM publisher WHERE name=%s", (pub_name,), one=True)
        if pub:
            pub_id = pub['publisher_id']
        else:
            pub_id = execute("INSERT INTO publisher (name) VALUES (%s)", (pub_name,))
    execute("""UPDATE book SET title=%s, isbn=%s, description=%s, cover_url=%s,
        total_pages=%s, publish_year=%s, score=%s, publisher_id=COALESCE(%s,publisher_id) WHERE book_id=%s""",
        (d.get('title'), d.get('isbn'), d.get('description'), d.get('cover'),
         d.get('total_pages'), d.get('publish_year'), d.get('score', 0), pub_id, book_id))
    # 更新作者（先删后插）
    author_str = (d.get('author') or '').strip()
    if author_str:
        execute("DELETE FROM book_author WHERE book_id=%s", (book_id,))
        for name in author_str.split('/'):
            name = name.strip()
            if not name: continue
            a = query("SELECT author_id FROM author WHERE name=%s", (name,), one=True)
            if a:
                aid = a['author_id']
            else:
                aid = execute("INSERT INTO author (name) VALUES (%s)", (name,))
            execute("INSERT INTO book_author (book_id, author_id, sort_order) VALUES (%s,%s,%s)",
                    (book_id, aid, 0))
    return ok({'id': book_id})

@app.route('/api/v1/admin/books/<int:book_id>', methods=['DELETE'])
@admin_required_v1
def admin_delete_book(book_id):
    execute("UPDATE book SET status=0 WHERE book_id=%s", (book_id,))
    return ok({'id': book_id, 'status': 'deleted'})

# ── Users Management ──

@app.route('/api/v1/admin/users')
@admin_required_v1
def admin_users():
    page = int(request.args.get('page', 1))
    size = int(request.args.get('size', 20))
    keyword = request.args.get('keyword', '')
    status_filter = request.args.get('status', '')
    off = (page - 1) * size
    where = 'WHERE 1=1'
    params = []
    if keyword:
        where += ' AND (username LIKE %s OR email LIKE %s)'
        params.extend([f'%{keyword}%', f'%{keyword}%'])
    if status_filter == 'active':
        where += ' AND status=1'
    elif status_filter == 'banned':
        where += ' AND status=0'
    users = query(f"SELECT user_id, username, email, role, status, created_at FROM user {where} ORDER BY user_id DESC LIMIT %s OFFSET %s",
                  tuple(params) + (size, off))
    total = query(f"SELECT COUNT(*) AS n FROM user {where}", tuple(params), one=True)['n']
    items = [{'id': u['user_id'], 'username': u['username'], 'email': u.get('email'),
              'role': u['role'], 'status': 'active' if u['status'] == 1 else 'banned',
              'created_at': str(u.get('created_at', ''))} for u in users]
    return ok({'items': items, 'total': total, 'page': page, 'size': size})

@app.route('/api/v1/admin/users/<int:user_id>/status', methods=['PUT'])
@admin_required_v1
def admin_update_user_status(user_id):
    d = request.get_json()
    new_status = 1 if d.get('status') == 'active' else 0
    execute("UPDATE user SET status=%s WHERE user_id=%s", (new_status, user_id))
    return ok({'id': user_id, 'status': d.get('status')})

# ── Comments Management ──

@app.route('/api/v1/admin/comments')
@admin_required_v1
def admin_comments():
    page = int(request.args.get('page', 1))
    size = int(request.args.get('size', 20))
    book_id = request.args.get('book_id')
    status_filter = request.args.get('status')
    keyword = request.args.get('keyword', '').strip()
    off = (page - 1) * size
    where = "WHERE 1=1"
    params = []
    if book_id:
        where += " AND c.book_id=%s"; params.append(book_id)
    # 支持逗号分隔多状态
    if status_filter:
        statuses = [s.strip() for s in status_filter.split(',') if s.strip()]
        if len(statuses) == 1:
            where += " AND c.status=%s"; params.append(statuses[0])
        elif len(statuses) > 1:
            ph = ','.join(['%s'] * len(statuses))
            where += f" AND c.status IN ({ph})"
            params.extend(statuses)
    # 图书名称搜索
    if keyword:
        where += " AND b.title LIKE %s"
        params.append(f'%{keyword}%')
    comments = query(f"""
        SELECT c.*, b.title AS book_title, u.username,
               COALESCE(NULLIF(c.nickname,''), u.username, '豆瓣书友') AS display_name,
               COALESCE(c.comment_date, CAST(c.created_at AS CHAR)) AS display_date
        FROM comment c JOIN book b ON c.book_id=b.book_id
        LEFT JOIN user u ON c.user_id=u.user_id
        {where} ORDER BY c.created_at DESC LIMIT %s OFFSET %s
    """, tuple(params) + (size, off))
    # COUNT 补齐 JOIN（关键字搜索需要 book 表）
    total_from = "FROM comment c JOIN book b ON c.book_id=b.book_id" if keyword else "FROM comment c"
    total = query(f"SELECT COUNT(*) AS n {total_from} {where}", tuple(params), one=True)['n']
    items = [{'id': c['comment_id'], 'book_id': c['book_id'], 'book_title': c['book_title'],
              'content': c['content'][:200], 'username': c['display_name'],
              'likes': c['likes'], 'status': c['status'],
              'created_at': c['display_date']} for c in comments]
    return ok({'items': items, 'total': total, 'page': page, 'size': size})

@app.route('/api/v1/admin/comments/<int:comment_id>', methods=['DELETE'])
@admin_required_v1
def admin_delete_comment(comment_id):
    execute("UPDATE comment SET status='deleted' WHERE comment_id=%s", (comment_id,))
    return ok({'id': comment_id, 'status': 'deleted'})

@app.route('/api/v1/admin/comments/<int:comment_id>/pin', methods=['PUT'])
@admin_required_v1
def admin_pin_comment(comment_id):
    d = request.get_json()
    new_status = 'pinned' if d.get('pinned') else 'normal'
    execute("UPDATE comment SET status=%s WHERE comment_id=%s", (new_status, comment_id))
    return ok({'id': comment_id, 'pinned': d.get('pinned')})

# ── Purchase Links ──

@app.route('/api/v1/admin/purchase-links')
@admin_required_v1
def admin_purchase_links():
    book_id = request.args.get('book_id')
    page = int(request.args.get('page', 1))
    size = int(request.args.get('size', 50))
    off = (page - 1) * size
    if book_id:
        links = query("SELECT pl.*, b.title AS book_title FROM purchase_link pl JOIN book b ON pl.book_id=b.book_id WHERE pl.book_id=%s ORDER BY pl.link_id", (book_id,))
        total = len(links)
    else:
        links = query("SELECT pl.*, b.title AS book_title FROM purchase_link pl JOIN book b ON pl.book_id=b.book_id ORDER BY pl.book_id LIMIT %s OFFSET %s", (size, off))
        total = query("SELECT COUNT(*) AS n FROM purchase_link", one=True)['n']
    items = [{'id': l['link_id'], 'book_id': l['book_id'], 'platform': l['platform'],
              'url': l['url'], 'price': float(l['price']) if l.get('price') else None,
              'book_title': l.get('book_title', '')} for l in links]
    return ok({'items': items, 'total': total, 'page': page, 'size': size})

@app.route('/api/v1/admin/purchase-links', methods=['POST'])
@admin_required_v1
def admin_create_purchase_link():
    d = request.get_json()
    lid = execute("INSERT INTO purchase_link (book_id, platform, url, price) VALUES (%s,%s,%s,%s) ON DUPLICATE KEY UPDATE url=VALUES(url), price=VALUES(price)",
                  (d['book_id'], d['platform'], d['url'], d.get('price')))
    return ok({'id': lid})

@app.route('/api/v1/admin/purchase-links/<int:link_id>', methods=['PUT'])
@admin_required_v1
def admin_update_purchase_link(link_id):
    d = request.get_json()
    execute("UPDATE purchase_link SET platform=%s, url=%s, price=%s WHERE link_id=%s",
            (d['platform'], d['url'], d.get('price'), link_id))
    return ok({'id': link_id})

@app.route('/api/v1/admin/purchase-links/<int:link_id>', methods=['DELETE'])
@admin_required_v1
def admin_delete_purchase_link(link_id):
    execute("DELETE FROM purchase_link WHERE link_id=%s", (link_id,))
    return ok({'id': link_id})

# ── Graph Stats ──

@app.route('/api/v1/admin/overview')
@admin_required_v1
def admin_overview():
    """系统概览：统计卡片 + 标签词云 + 最新动态"""
    book_total = query("SELECT COUNT(*) AS n FROM book WHERE status=1", one=True)['n']
    user_total = query("SELECT COUNT(*) AS n FROM user", one=True)['n']
    author_total = query("SELECT COUNT(*) AS n FROM author", one=True)['n']
    tag_total = query("SELECT COUNT(*) AS n FROM tag", one=True)['n']
    publisher_total = query("SELECT COUNT(*) AS n FROM publisher", one=True)['n']
    comment_total = query("SELECT COUNT(*) AS n FROM comment WHERE status IN ('normal','pinned')", one=True)['n']
    rating_total = query("SELECT COUNT(*) AS n FROM rating", one=True)['n']
    chapter_total = query("SELECT COUNT(*) AS n FROM book_chapter", one=True)['n']

    tag_cloud = query("""
        SELECT t.name, COUNT(bt.book_id) AS cnt
        FROM tag t JOIN book_tag bt ON t.tag_id = bt.tag_id
        GROUP BY t.tag_id ORDER BY cnt DESC LIMIT 60
    """)

    recent_comments = query("""
        SELECT c.comment_id, c.content, c.created_at, c.likes,
               b.title AS book_title, COALESCE(NULLIF(c.nickname,''), u.username, '豆瓣书友') AS username
        FROM comment c JOIN book b ON c.book_id = b.book_id
        LEFT JOIN user u ON c.user_id = u.user_id
        WHERE c.status IN ('normal','pinned') AND c.user_id != 1
        ORDER BY c.created_at DESC LIMIT 15
    """)

    recent_users = query("SELECT user_id, username, created_at FROM user ORDER BY created_at DESC LIMIT 10")

    new_books_30d = query("SELECT COUNT(*) AS n FROM book WHERE status=1 AND created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)", one=True)['n']
    new_comments_30d = query("SELECT COUNT(*) AS n FROM comment WHERE status IN ('normal','pinned') AND created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)", one=True)['n']

    return ok({
        'basic': {
            'books': book_total, 'users': user_total, 'authors': author_total,
            'tags': tag_total, 'publishers': publisher_total,
            'comments': comment_total, 'ratings': rating_total, 'chapters': chapter_total,
        },
        'tagCloud': [{'name': r['name'], 'value': r['cnt']} for r in tag_cloud],
        'recentComments': [{
            'id': r['comment_id'], 'content': (r['content'] or '')[:100],
            'time': str(r['created_at']), 'likes': r['likes'],
            'book': r['book_title'], 'user': r['username']
        } for r in recent_comments],
        'recentUsers': [{'id': r['user_id'], 'name': r['username'], 'time': str(r['created_at'])} for r in recent_users],
        'trends': {'newBooks30d': new_books_30d, 'newComments30d': new_comments_30d},
    })

@app.route('/api/v1/admin/activity')
@admin_required_v1
def admin_activity():
    """用户活跃度：?mode=monthly|weekly|daily&offset=-1"""
    from datetime import date, timedelta
    mode = request.args.get('mode', 'weekly')
    offset = int(request.args.get('offset', 0))
    today = date.today()
    NOT_IMPORT = " AND user_id != 1"

    cfg = get_mysql_cfg()
    conn = pymysql.connect(**cfg, cursorclass=pymysql.cursors.DictCursor)
    cur = conn.cursor()

    if mode == 'monthly':
        keys, labels = [], []
        start_month = today.month + offset
        start_year = today.year
        while start_month <= 0: start_month += 12; start_year -= 1
        while start_month > 12: start_month -= 12; start_year += 1
        for i in range(12):
            m = start_month + i; y = start_year
            while m > 12: m -= 12; y += 1
            while m <= 0: m += 12; y -= 1
            keys.append(f'{y}-{m:02d}'); labels.append(f'{m}月')
        def _query(table, date_col):
            extra = "AND status IN ('normal','pinned')" if table == 'comment' else ''
            ni = NOT_IMPORT if table in ('comment','rating') else ''
            cur.execute(f"SELECT DATE_FORMAT({date_col}, '%Y-%m') AS period, COUNT(*) AS cnt FROM {table} WHERE 1=1 {extra} {ni} GROUP BY period")
            return {r['period']: r['cnt'] for r in cur.fetchall()}
    elif mode == 'daily':
        keys = [f'{h:02d}' for h in range(24)]
        target_date = today + timedelta(days=offset)
        labels = [f'{h:02d}:00' for h in range(24)]
        def _query(table, date_col):
            extra = "AND status IN ('normal','pinned')" if table == 'comment' else ''
            ni = NOT_IMPORT if table in ('comment','rating') else ''
            cur.execute(f"SELECT HOUR({date_col}) AS period, COUNT(*) AS cnt FROM {table} WHERE 1=1 {extra} {ni} AND DATE({date_col})=DATE('{target_date}') GROUP BY period")
            return {str(r['period']).zfill(2): r['cnt'] for r in cur.fetchall()}
    else:
        monday = today - timedelta(days=today.weekday()) + timedelta(weeks=offset)
        days_char = ['周一','周二','周三','周四','周五','周六','周日']
        keys, labels = [], []
        for i in range(7):
            d = monday + timedelta(days=i)
            keys.append(d.strftime('%Y-%m-%d'))
            labels.append(f'{days_char[i]} {d.month}/{d.day}')
        def _query(table, date_col):
            extra = "AND status IN ('normal','pinned')" if table == 'comment' else ''
            ni = NOT_IMPORT if table in ('comment','rating') else ''
            cur.execute(f"SELECT DATE({date_col}) AS period, COUNT(*) AS cnt FROM {table} WHERE 1=1 {extra} {ni} AND {date_col} >= '{monday}' AND {date_col} < '{monday + timedelta(days=7)}' GROUP BY period")
            return {str(r['period']): r['cnt'] for r in cur.fetchall()}

    cmap = _query('comment', 'created_at')
    rmap = _query('rating', 'created_at')
    bmap = _query('user_behavior', 'created_at')
    rdmap = _query('reading_progress', 'updated_at')
    cur.close(); conn.close()

    items = []; total_sum = 0
    for i, key in enumerate(keys):
        c = cmap.get(key, 0); r = rmap.get(key, 0)
        b = bmap.get(key, 0); rd = rdmap.get(key, 0)
        t = c + r + b + rd; total_sum += t
        items.append({'period': key, 'label': labels[i], 'total': t,
                      'comment': c, 'rating': r, 'login': b, 'reading': rd})

    peak = max(items, key=lambda x: x['total']) if items else None
    return ok({
        'mode': mode, 'items': items,
        'peakLabel': peak['label'] if peak else '-',
        'peakCount': peak['total'] if peak else 0,
        'avgCount': round(total_sum / len(items), 1) if items else 0,
        'totalCount': total_sum,
        'dateLabel': target_date.strftime('%Y年%m月%d日') if mode == 'daily' else '',
    })

@app.route('/api/v1/admin/graph/stats')
@admin_required_v1
def admin_graph_stats():
    book_count = query("SELECT COUNT(*) AS n FROM book WHERE status=1", one=True)['n']
    author_count = query("SELECT COUNT(*) AS n FROM author", one=True)['n']
    tag_count = query("SELECT COUNT(*) AS n FROM tag", one=True)['n']
    user_count = query("SELECT COUNT(*) AS n FROM user", one=True)['n']
    comment_count = query("SELECT COUNT(*) AS n FROM comment WHERE status='normal'", one=True)['n']
    rating_count = query("SELECT COUNT(*) AS n FROM rating", one=True)['n']
    return ok({
        'nodes': {'book': book_count, 'author': author_count, 'tag': tag_count, 'user': user_count},
        'relations': {'comments': comment_count, 'ratings': rating_count},
        'total_books': book_count, 'total_users': user_count,
    })

@app.route('/api/v1/admin/graph/data')
@admin_required_v1
def admin_graph_data():
    """搜索驱动的自我中心网络可视化
    支持参数：
      - popular=1         → 返回热门实体（用于搜索框占位推荐）
      - keyword=xxx       → 跨类型搜索（图书/作者/出版社/标签）
      - book_id=123       → 以图书为中心的 1-hop / 2-hop 网络
      - author=xxx        → 以作者为中心的网络
      - publisher=xxx     → 以出版社为中心的网络
      - tag=xxx           → 以标签为中心的网络
      - depth=1|2         → 展开深度（默认1）
    无参数时返回空网络 + 统计信息
    标签以推荐系统（MySQL tag 表）为准
    """
    book_id = request.args.get('book_id', type=int)
    author_name = request.args.get('author', '').strip()
    publisher_name = request.args.get('publisher', '').strip()
    tag_name = request.args.get('tag', '').strip()
    keyword = request.args.get('keyword', '').strip()
    depth = request.args.get('depth', 1, type=int)
    popular = request.args.get('popular', type=int)

    categories = [
        {'name': '图书', 'itemStyle': {'color': '#D4A24C'}},
        {'name': '作者', 'itemStyle': {'color': '#3498DB'}},
        {'name': '标签', 'itemStyle': {'color': '#2ECC71'}},
        {'name': '出版社', 'itemStyle': {'color': '#9B59B6'}},
    ]

    # ── 热门实体 ──
    if popular:
        try:
            from recommendation.config import get_neo4j_cfg
            cfg = get_neo4j_cfg()
            from neo4j import GraphDatabase
            driver = GraphDatabase.driver(cfg['uri'], auth=(cfg['user'], cfg['password']))
            with driver.session(database=cfg.get('database','neo4j')) as s:
                pop_authors, pop_tags, pop_publishers = [], [], []
                for r in s.run("MATCH (a:Author)<-[:WRITTEN_BY]-(b:Book) RETURN a.name AS name, count(b) AS cnt ORDER BY cnt DESC LIMIT 8"):
                    pop_authors.append({'name': clean_graph_name(r['name']), 'cnt': r['cnt']})
                for r in s.run("MATCH (t:Tag)<-[:HAS_TAG]-(b:Book) RETURN t.name AS name, count(b) AS cnt ORDER BY cnt DESC LIMIT 8"):
                    pop_tags.append({'name': clean_graph_name(r['name']), 'cnt': r['cnt']})
                for r in s.run("MATCH (p:Publisher)<-[:PUBLISHED_BY]-(b:Book) RETURN p.name AS name, count(b) AS cnt ORDER BY cnt DESC LIMIT 8"):
                    pop_publishers.append({'name': clean_graph_name(r['name']), 'cnt': r['cnt']})
            driver.close()
        except Exception as e:
            print(f'Neo4j popular query failed: {e}')
            pop_authors, pop_tags, pop_publishers = [], [], []
        return ok({
            'type': 'popular',
            'authors': pop_authors, 'tags': pop_tags, 'publishers': pop_publishers,
            'categories': categories,
        })

    # ── 关键词搜索（跨类型） ──
    if keyword:
        books = query(
            "SELECT book_id, title, score FROM book WHERE title LIKE %s AND status=1 ORDER BY score DESC LIMIT 10",
            (f'%{keyword}%',))
        authors = query(
            "SELECT author_id, name FROM author WHERE name LIKE %s LIMIT 8",
            (f'%{keyword}%',))
        publishers = query(
            "SELECT publisher_id, name FROM publisher WHERE name LIKE %s LIMIT 6",
            (f'%{keyword}%',))
        tags = query(
            "SELECT tag_id, name FROM tag WHERE name LIKE %s LIMIT 8",
            (f'%{keyword}%',))
        return ok({
            'type': 'search_results',
            'books': [{'book_id': b['book_id'], 'title': b['title'], 'score': float(b['score'] or 0)} for b in books],
            'authors': [{'author_id': a['author_id'], 'name': a['name']} for a in authors],
            'publishers': [{'publisher_id': p['publisher_id'], 'name': p['name']} for p in publishers],
            'tags': [{'tag_id': t['tag_id'], 'name': t['name']} for t in tags],
        })

    # ── 无参数时：返回 Top10 高分书籍的自我中心网络 ──
    if not book_id and not author_name and not publisher_name and not tag_name:
        top_books = query("SELECT book_id, douban_id, title, score FROM book "
                          "WHERE status=1 ORDER BY score DESC LIMIT 10")
        try:
            from recommendation.config import get_neo4j_cfg
            cfg = get_neo4j_cfg()
            from neo4j import GraphDatabase
            driver = GraphDatabase.driver(cfg['uri'], auth=(cfg['user'], cfg['password']))
            _nodes = []
            _links = []
            _node_ids = set()
            def _add_node(nid, name, category, score=None):
                if nid not in _node_ids:
                    _node_ids.add(nid)
                    sz = max(20, min(50, (score or 5) * 5)) if category == 'book' else (18 if category == 'author' else 14)
                    _nodes.append({'id': nid, 'name': str(name)[:40], 'category': category, 'symbolSize': sz})
            with driver.session(database=cfg.get('database','neo4j')) as s:
                for b in top_books:
                    douban_id = str(b['douban_id'])
                    seed_id = 'book_' + douban_id
                    _add_node(seed_id, b['title'], 'book', float(b['score'] or 0))
                    for r in s.run("MATCH (b:Book {book_id:$bid})-[:WRITTEN_BY]->(a:Author) RETURN a.name AS n", bid=douban_id):
                        cn = clean_graph_name(r['n'])
                        _add_node('author_'+cn, cn, 'author')
                        _links.append({'source': seed_id, 'target': 'author_'+cn, 'label': '作者'})
                    for r in s.run("MATCH (b:Book {book_id:$bid})-[:HAS_TAG]->(t:Tag) RETURN t.name AS n", bid=douban_id):
                        cn = clean_graph_name(r['n'])
                        _add_node('tag_'+cn, cn, 'tag')
                        _links.append({'source': seed_id, 'target': 'tag_'+cn, 'label': '标签'})
                    for r in s.run("MATCH (b:Book {book_id:$bid})-[:PUBLISHED_BY]->(p:Publisher) RETURN p.name AS n", bid=douban_id):
                        cn = clean_graph_name(r['n'])
                        _add_node('publisher_'+cn, cn, 'publisher')
                        _links.append({'source': seed_id, 'target': 'publisher_'+cn, 'label': '出版社'})
            driver.close()
            return ok({
                'type': 'top10_overview',
                'nodes': _nodes, 'links': _links,
                'node_stats': {
                    'book': sum(1 for n in _nodes if n['category']=='book'),
                    'author': sum(1 for n in _nodes if n['category']=='author'),
                    'tag': sum(1 for n in _nodes if n['category']=='tag'),
                    'publisher': sum(1 for n in _nodes if n['category']=='publisher'),
                },
                'categories': categories,
                'source': 'neo4j'
            })
        except Exception as e:
            print(f"KG top10 error: {e}")
            book_count = query("SELECT COUNT(*) AS n FROM book WHERE status=1", one=True)['n']
            return ok({
                'type': 'empty',
                'total_books': book_count,
                'nodes': {'book': book_count, 'author': 0, 'tag': 0, 'publisher': 0},
                'categories': categories,
            })

    # ── 自我中心网络 ──
    try:
        from recommendation.config import get_neo4j_cfg
        cfg = get_neo4j_cfg()
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver(cfg['uri'], auth=(cfg['user'], cfg['password']))
        nodes = []
        links = []
        node_ids = set()

        def add_node(nid, name, category, score=None, mysql_id=None):
            if nid not in node_ids:
                node_ids.add(nid)
                if category == 'book':
                    size = max(20, min(50, (score or 5) * 5))
                elif category == 'author':
                    size = 18
                else:
                    size = 14
                nd = {'id': nid, 'name': str(name)[:40], 'category': category, 'symbolSize': size}
                if mysql_id:
                    nd['mysql_id'] = mysql_id
                nodes.append(nd)

        with driver.session(database=cfg.get('database','neo4j')) as s:
            if book_id:
                # 以图书为中心：1-hop（作者/标签/出版社）+ 2-hop（同作者/同标签的其他书）
                book_row = query(
                    "SELECT book_id, douban_id, title, score FROM book WHERE book_id=%s",
                    (book_id,), one=True)
                if not book_row:
                    driver.close()
                    return err('图书不存在', 404)
                douban_id = str(book_row['douban_id'])
                seed = s.run(
                    'MATCH (b:Book {book_id: $bid}) RETURN b.book_id AS bid, b.title AS title, b.score AS score',
                    bid=douban_id).single()
                if not seed:
                    driver.close()
                    return err('该图书尚未导入 Neo4j 知识图谱', 404)

                seed_id = 'book_' + douban_id
                add_node(seed_id, seed['title'], 'book', float(seed['score'] or 0), mysql_id=book_row['book_id'])

                # 一度关系：作者、标签、出版社
                for r in s.run(
                    "MATCH (b:Book {book_id:$bid})-[rel:WRITTEN_BY]->(a:Author) RETURN a.name AS n",
                    bid=douban_id):
                    clean = clean_graph_name(r['n'])
                    aid = 'author_' + clean
                    add_node(aid, clean, 'author')
                    links.append({'source': seed_id, 'target': aid, 'label': '作者'})

                for r in s.run(
                    "MATCH (b:Book {book_id:$bid})-[rel:HAS_TAG]->(t:Tag) RETURN t.name AS n",
                    bid=douban_id):
                    clean = clean_graph_name(r['n'])
                    tid = 'tag_' + clean
                    add_node(tid, clean, 'tag')
                    links.append({'source': seed_id, 'target': tid, 'label': '标签'})

                for r in s.run(
                    "MATCH (b:Book {book_id:$bid})-[rel:PUBLISHED_BY]->(p:Publisher) RETURN p.name AS n",
                    bid=douban_id):
                    clean = clean_graph_name(r['n'])
                    pid = 'publisher_' + clean
                    add_node(pid, clean, 'publisher')
                    links.append({'source': seed_id, 'target': pid, 'label': '出版社'})

                # 二度关系：同作者/同标签的其他书
                if depth >= 2:
                    for r in s.run(
                        "MATCH (b:Book {book_id:$bid})-[:WRITTEN_BY]->(a:Author)<-[:WRITTEN_BY]-(o:Book) "
                        "WHERE o.book_id <> $bid RETURN o.book_id AS bid, o.title AS t, o.score AS s, a.name AS an",
                        bid=douban_id):
                        oid = 'book_' + str(r['bid'])
                        add_node(oid, r['t'], 'book', float(r['s'] or 0))
                        links.append({'source': 'author_' + clean_graph_name(r['an']), 'target': oid, 'label': '作者'})

                    for r in s.run(
                        "MATCH (b:Book {book_id:$bid})-[:HAS_TAG]->(t:Tag)<-[:HAS_TAG]-(o:Book) "
                        "WHERE o.book_id <> $bid RETURN o.book_id AS bid, o.title AS t, o.score AS s, t.name AS tn",
                        bid=douban_id):
                        oid = 'book_' + str(r['bid'])
                        add_node(oid, r['t'], 'book', float(r['s'] or 0))
                        links.append({'source': 'tag_' + clean_graph_name(r['tn']), 'target': oid, 'label': '标签'})

            elif author_name:
                # 以作者为中心：该作者的所有书 + 这些书的标签/出版社
                clean_author = clean_graph_name(author_name)
                aid = 'author_' + clean_author
                add_node(aid, clean_author, 'author')
                for r in s.run(
                    "MATCH (a:Author)<-[:WRITTEN_BY]-(b:Book) WHERE a.name CONTAINS $n "
                    "RETURN b.book_id AS bid, b.title AS t, b.score AS s LIMIT 50",
                    n=author_name):
                    oid = 'book_' + str(r['bid'])
                    add_node(oid, r['t'], 'book', float(r['s'] or 0))
                    links.append({'source': oid, 'target': aid, 'label': '作者'})
                    # 这些书的标签
                    if depth >= 2:
                        for tr in s.run(
                            "MATCH (b:Book {book_id:$bid})-[:HAS_TAG]->(t:Tag) RETURN t.name AS n",
                            bid=str(r['bid'])):
                            ct = clean_graph_name(tr['n'])
                            tid = 'tag_' + ct
                            add_node(tid, ct, 'tag')
                            links.append({'source': oid, 'target': tid, 'label': '标签'})

            elif publisher_name:
                # 以出版社为中心：该出版社的所有书
                clean_pub = clean_graph_name(publisher_name)
                pid = 'publisher_' + clean_pub
                add_node(pid, clean_pub, 'publisher')
                for r in s.run(
                    "MATCH (p:Publisher)<-[:PUBLISHED_BY]-(b:Book) WHERE p.name CONTAINS $n "
                    "RETURN b.book_id AS bid, b.title AS t, b.score AS s LIMIT 50",
                    n=publisher_name):
                    oid = 'book_' + str(r['bid'])
                    add_node(oid, r['t'], 'book', float(r['s'] or 0))
                    links.append({'source': oid, 'target': pid, 'label': '出版社'})

            elif tag_name:
                # 以标签为中心：该标签下的所有书（使用推荐系统 MySQL 标签名）
                clean_tag = clean_graph_name(tag_name)
                tid = 'tag_' + clean_tag
                add_node(tid, clean_tag, 'tag')
                for r in s.run(
                    "MATCH (t:Tag)<-[:HAS_TAG]-(b:Book) WHERE t.name CONTAINS $n "
                    "RETURN b.book_id AS bid, b.title AS t, b.score AS s LIMIT 50",
                    n=tag_name):
                    oid = 'book_' + str(r['bid'])
                    add_node(oid, r['t'], 'book', float(r['s'] or 0))
                    links.append({'source': oid, 'target': tid, 'label': '标签'})
                    # 这些书的作者
                    if depth >= 2:
                        for ar in s.run(
                            "MATCH (b:Book {book_id:$bid})-[:WRITTEN_BY]->(a:Author) RETURN a.name AS n",
                            bid=str(r['bid'])):
                            ca = clean_graph_name(ar['n'])
                            aid = 'author_' + ca
                            add_node(aid, ca, 'author')
                            links.append({'source': oid, 'target': aid, 'label': '作者'})

        driver.close()

        # 为所有 book 节点反查 MySQL book_id（支持点击跳转）
        douban_ids_in_graph = [n['id'].replace('book_', '') for n in nodes
                               if n['id'].startswith('book_') and 'mysql_id' not in n]
        if douban_ids_in_graph:
            placeholders = ','.join(['%s'] * len(douban_ids_in_graph))
            mapping_rows = query(
                f"SELECT book_id, douban_id FROM book WHERE douban_id IN ({placeholders})",
                douban_ids_in_graph)
            d2m = {str(r['douban_id']): r['book_id'] for r in mapping_rows}
            for n in nodes:
                if n['id'].startswith('book_') and 'mysql_id' not in n:
                    douban = n['id'].replace('book_', '')
                    if douban in d2m:
                        n['mysql_id'] = d2m[douban]

        if nodes:
            return ok({'type': 'ego_network', 'nodes': nodes, 'links': links,
                        'categories': categories, 'source': 'neo4j'})
    except Exception as e:
        print(f'Neo4j ego-network query failed: {e}')
        import traceback
        traceback.print_exc()

    # MySQL 降级（原来的降级逻辑保留）

# ═══════════ FRONTEND ═══════════

@app.route('/')
def index():
    u = get_user()
    sort = request.args.get('sort','score')
    order = {'score':'b.score DESC','pages':'b.total_pages DESC','year':'b.publish_year DESC'}.get(sort,'b.score DESC')
    books = query(f"""
        SELECT b.book_id, b.title, b.score, b.description,
               ANY_VALUE(a.name) AS author, ANY_VALUE(p.name) AS publisher
        FROM book b
        LEFT JOIN book_author ba ON b.book_id=ba.book_id AND ba.sort_order=0
        LEFT JOIN author a ON ba.author_id=a.author_id
        LEFT JOIN publisher p ON b.publisher_id=p.publisher_id
        GROUP BY b.book_id ORDER BY {order}
    """)
    hot = query("SELECT book_id, title, score FROM book ORDER BY score DESC LIMIT 10")

    personalized = []
    if u:
        try:
            shelf = query("SELECT b.book_id, b.douban_id FROM bookshelf_item bsi JOIN bookshelf bs ON bsi.shelf_id=bs.shelf_id JOIN book b ON bsi.book_id=b.book_id WHERE bs.user_id=%s LIMIT 5", (u['user_id'],))
            if shelf:
                engine = get_engine()
                seen = set()
                for sb in shelf:
                    try:
                        for r in engine.recommend_for_book(sb['book_id'], 3):
                            if r['douban_id'] not in seen:
                                seen.add(r['douban_id'])
                                rb = query("SELECT book_id, title, score FROM book WHERE douban_id=%s", (r['douban_id'],), one=True)
                                if rb: personalized.append({'book_id':rb['book_id'], 'title':rb['title'], 'score':rb['score'], 'reason':r['reason']})
                    except: pass
        except: pass

    body = ''
    if personalized:
        body += '<div class="section-title">👤 为你推荐</div><div class="grid">'
        for b in personalized:
            body += f'<div class="card"><a href="/book/{b["book_id"]}" style="text-decoration:none;color:inherit"><h3>{b["title"]}</h3><div class="score">★ {b["score"]}</div><div class="reason">{b["reason"]}</div></a></div>'
        body += '</div>'

    body += '<div class="section-title">🔥 热门推荐</div><div class="grid">'
    for b in hot:
        body += f'<div class="card"><a href="/book/{b["book_id"]}" style="text-decoration:none;color:inherit"><h3>{b["title"]}</h3><div class="score">★ {b["score"]}</div></a></div>'
    body += '</div>'

    body += '<div class="flex-row" style="margin:16px 0"><a href="/?sort=score" class="btn btn-sm btn-outline">按评分</a><a href="/?sort=pages" class="btn btn-sm btn-outline">按页数</a><a href="/?sort=year" class="btn btn-sm btn-outline">按出版年</a></div>'
    body += '<div class="grid">'
    for b in books:
        body += f'<div class="card"><a href="/book/{b["book_id"]}" style="text-decoration:none;color:inherit"><h3>{b["title"]}</h3><div class="meta">{b.get("author","")} / {b.get("publisher","")}</div><div class="score">★ {b["score"]}</div>'
        if b.get('description'): body += f'<div class="desc">{b["description"][:100]}</div>'
        body += '</a></div>'
    body += '</div>'
    return page('豆瓣Top250 荐书', body, u)


@app.route('/book/<int:book_id>')
def detail(book_id):
    u = get_user()
    b = query("""
        SELECT b.*, a.name AS author, p.name AS publisher
        FROM book b LEFT JOIN book_author ba ON b.book_id=ba.book_id AND ba.sort_order=0
        LEFT JOIN author a ON ba.author_id=a.author_id LEFT JOIN publisher p ON b.publisher_id=p.publisher_id
        WHERE b.book_id=%s
    """, (book_id,), one=True)
    if not b: return 'Not found', 404

    comments = query("""
        SELECT c.*, COALESCE(NULLIF(c.nickname,''), CASE WHEN c.user_id=1 THEN '豆瓣书友' ELSE COALESCE(u.username,'匿名') END) AS username,
               COALESCE(c.comment_date, CAST(c.created_at AS CHAR)) AS display_date
        FROM comment c LEFT JOIN user u ON c.user_id=u.user_id
        WHERE c.book_id=%s AND c.status='normal' ORDER BY c.likes DESC LIMIT 10
    """, (book_id,))

    shelf_status = None
    if u:
        s = query("SELECT read_status FROM bookshelf_item bsi JOIN bookshelf bs ON bsi.shelf_id=bs.shelf_id WHERE bs.user_id=%s AND bsi.book_id=%s",
                  (u['user_id'], book_id), one=True)
        if s: shelf_status = s['read_status']
        ur = query("SELECT score FROM rating WHERE user_id=%s AND book_id=%s", (u['user_id'], book_id), one=True)
        user_rating = ur['score'] if ur else None
    else:
        user_rating = None

    similar = []
    try:
        engine = get_engine()
        for r in engine.recommend_for_book(book_id, 8):
            rb = query("SELECT book_id, title, score FROM book WHERE douban_id=%s", (r['douban_id'],), one=True)
            if rb: similar.append({'book_id':rb['book_id'],'title':rb['title'],'score':round(r['score'],2),'reason':r['reason']})
    except: pass

    body = f'''<div style="max-width:800px;margin:0 auto">
    <a href="javascript:history.back()" style="color:#d4a24c">← 返回上一页</a>
    <div class="card" style="margin:16px 0">
      <h1>{b["title"]}</h1>
      <div class="meta">{b.get("author","")} / {b.get("publisher","")}</div>
      <div class="meta">ISBN: {b.get("isbn") or "-"} · {b.get("total_pages") or "-"}页 · {b.get("binding") or "-"} · {b.get("publish_year") or ""}</div>
      <div class="score" style="font-size:20px">★ {b["score"]}</div>
      ''' + (rating_stars_html(book_id, user_rating) if u else '') + f'''
      {"<p style='margin-top:12px;line-height:1.8;color:#555'>"+b["description"]+"</p>" if b.get("description") else ""}'''

    if u:
        body += f'''<div class="flex-row" style="margin-top:12px">
        <button class="btn btn-outline btn-sm" onclick="shelfAction({book_id},'want_to_read')">📖 想读</button>
        <button class="btn btn-outline btn-sm" onclick="shelfAction({book_id},'reading')">📘 在读</button>
        <button class="btn btn-outline btn-sm" onclick="shelfAction({book_id},'finished')">✅ 已读</button>'''
        if shelf_status:
            label = {'want_to_read':'想读','reading':'在读','finished':'已读'}.get(shelf_status,shelf_status)
            body += f'<span class="badge">当前: {label}</span>'
        body += '</div>'
    body += '</div>'

    if similar:
        body += '<div class="section-title">🤝 相似推荐</div><div class="grid">'
        for s in similar:
            body += f'''<div class="card"><a href="/book/{s["book_id"]}" style="text-decoration:none;color:inherit"><h3>{s["title"]}</h3><div class="score">★ {s["score"]}</div><div class="reason">{s["reason"]}</div></a>'''
            if u: body += f'<div class="flex-row" style="margin-top:6px"><button class="btn btn-sm btn-outline" onclick="feedback({s["book_id"]},\'interested\',event)">👍 感兴趣</button><button class="btn btn-sm btn-outline" onclick="feedback({s["book_id"]},\'not_interested\',event)">👎 不感兴趣</button></div>'
            body += '</div>'
        body += '</div>'

    # Purchase links (show for all books)
    pu_links = query("SELECT platform, url, price FROM purchase_link WHERE book_id=%s ORDER BY price", (book_id,))
    if not pu_links:
        # auto-generate link for any book
        encoded = quote(b["title"])
        body += f'<div class="section-title">🛒 购买实体书</div><div class="flex-row"><a href="https://search.jd.com/Search?keyword={encoded}" target="_blank" class="btn btn-outline btn-sm">京东</a><a href="http://search.dangdang.com/?key={encoded}" target="_blank" class="btn btn-outline btn-sm">当当</a></div>'
    else:
        body += '<div class="section-title">🛒 购买实体书</div><div class="flex-row">'
        for pl in pu_links:
            body += f'<a href="{pl["url"]}" target="_blank" class="btn btn-outline btn-sm">{pl["platform"]} ¥{pl["price"] or "?"}</a>'
        body += '</div>'

    body += f'<div class="section-title">💬 评论 ({len(comments)})</div>'
    if u:
        body += f'''<div style="margin-bottom:12px"><textarea id="cmt-input" rows="3" style="width:100%;padding:10px;border:1px solid #ddd;border-radius:8px" placeholder="写评论..."></textarea>
        <button class="btn btn-primary btn-sm" onclick="postComment({book_id})" style="margin-top:6px">发表</button></div>'''
    for c in comments:
        body += f'''<div class="card" style="margin-bottom:8px">
        <div class="meta"><strong>{c["username"]}</strong> · {c.get("display_date","")} · ❤️ <span id="likes-{c["comment_id"]}">{c["likes"]}</span>'''
        if u: body += f'<button class="btn btn-sm btn-outline" onclick="likeComment({c["comment_id"]})">👍</button>'
        body += f'</div><p style="margin-top:6px;color:#444">{c["content"]}</p></div>'
    body += '</div>'

    body += '''<script>
    async function shelfAction(bid,status){var r=await api("/api/shelf/add",{book_id:bid,status:status});if(r.ok)toast("已加入书架");}
    async function postComment(bid){var txt=document.getElementById("cmt-input").value;if(!txt)return;var r=await api("/api/comment/post",{book_id:bid,content:txt});if(r.ok){toast("评论成功");setTimeout(function(){location.reload()},1200)}else{toast("发表失败")}}
    async function likeComment(cid){await api("/api/comment/like",{comment_id:cid});var el=document.getElementById("likes-"+cid);el.textContent=parseInt(el.textContent)+1;toast("已点赞")}
    async function feedback(bid,action,evt){evt.preventDefault();evt.stopPropagation();await api("/api/rec/feedback",{book_id:bid,action:action});toast(action==="interested"?"已标记感兴趣":"已标记不感兴趣")}
    async function rateBook(bid,score){var r=await api("/api/rate",{book_id:bid,score:score});if(r.ok){toast("已评分 "+score+" 星");setTimeout(function(){location.reload()},500)}}
    </script>'''
    return page(b['title'], body, u)


@app.route('/shelf')
@login_required
def shelf_page():
    u = get_user()
    items = query("""
        SELECT bsi.*, b.title, b.score, b.book_id FROM bookshelf_item bsi
        JOIN bookshelf bs ON bsi.shelf_id=bs.shelf_id JOIN book b ON bsi.book_id=b.book_id
        WHERE bs.user_id=%s
    """, (u['user_id'],))
    body = '<h2>📚 我的书架</h2><div class="grid">'
    for it in items:
        label = {'want_to_read':'想读','reading':'在读','finished':'已读'}.get(it['read_status'],it['read_status'])
        body += f'''<div class="card"><a href="/book/{it['book_id']}" style="text-decoration:none;color:inherit">
        <h3>{it['title']}</h3><div class="score">★ {it['score']}</div><div class="badge">{label}</div></a>
        <button class="btn btn-danger btn-sm" style="margin-top:4px" onclick="removeFromShelf({it['book_id']})">移除</button></div>'''
    body += '</div><script>async function removeFromShelf(bid){await api("/api/shelf/remove",{book_id:bid});location.reload()}</script>'
    return page('我的书架', body, u)


if __name__ == '__main__':
    print("\n" + "="*50)
    print("  基于知识图谱的个性化荐书系统")
    print("  http://localhost:5000")
    print("="*50 + "\n")
    app.run(host='0.0.0.0', port=5000, debug=True)
