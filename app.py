# -*- coding: utf-8 -*-
"""
河南农业大学校园专属闲置物品交易平台
技术栈：Python + Flask + SQLite + 原生HTML
Render 部署版本
"""

from flask import Flask, render_template, request, redirect, url_for, session, jsonify, g
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
from datetime import datetime
from functools import wraps

app = Flask(__name__)

# ==================== Render 环境配置 ====================
# 从环境变量读取密钥，如果没有则使用默认（仅用于开发）
app.secret_key = os.environ.get('SECRET_KEY', 'hnau_market_secret_key_2024')

# 数据库路径：Render 免费版使用 /tmp 目录（适合数据不持久化的场景）
# 如果需要持久化，可以使用 $RENDER_DISK_PATH 但免费版不支持
# 这里使用环境变量允许自定义
DATABASE_PATH = os.environ.get('DATABASE_PATH', '/tmp/hnau_market.db')

# 获取 Render 分配的端口，或默认 5000
PORT = int(os.environ.get('PORT', 5000))

# ==================== 数据库相关 ====================

def get_db():
    """获取数据库连接"""
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE_PATH)
        g.db.row_factory = sqlite3.Row  # 返回字典格式
    return g.db

@app.teardown_appcontext
def close_db(error):
    """关闭数据库连接"""
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    """初始化数据库表"""
    db = get_db()
    
    # 用户表
    db.execute('''
        CREATE TABLE IF NOT EXISTS user (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            phone TEXT,
            email TEXT,
            auth_status TEXT DEFAULT '未认证',
            student_id TEXT,
            college TEXT,
            student_card_url TEXT,
            is_admin INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 闲置物品表（增加成色字段）
    db.execute('''
        CREATE TABLE IF NOT EXISTS item (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            category TEXT,
            price REAL,
            condition TEXT DEFAULT '9成新',
            image_url TEXT,
            contact TEXT,
            description TEXT,
            status TEXT DEFAULT '在售',
            user_id INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES user (id)
        )
    ''')
    
    # 为已存在的item表添加condition字段（如果不存在）
    try:
        db.execute("ALTER TABLE item ADD COLUMN condition TEXT DEFAULT '9成新'")
        db.commit()
    except:
        pass  # 字段已存在
    
    # 收藏表
    db.execute('''
        CREATE TABLE IF NOT EXISTS favorite (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            item_id INTEGER NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES user (id),
            FOREIGN KEY (item_id) REFERENCES item (id),
            UNIQUE(user_id, item_id)
        )
    ''')
    
    # 浏览历史表
    db.execute('''
        CREATE TABLE IF NOT EXISTS browse_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            item_id INTEGER NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES user (id),
            FOREIGN KEY (item_id) REFERENCES item (id)
        )
    ''')
    
    # 留言表
    db.execute('''
        CREATE TABLE IF NOT EXISTS comment (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            reply_to INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (item_id) REFERENCES item (id),
            FOREIGN KEY (user_id) REFERENCES user (id),
            FOREIGN KEY (reply_to) REFERENCES comment (id)
        )
    ''')
    
    # 创建默认管理员账号
    cursor = db.execute('SELECT id FROM user WHERE username = ?', ('admin',))
    if cursor.fetchone() is None:
        hashed_password = generate_password_hash('admin123')
        db.execute('''
            INSERT INTO user (username, password, auth_status, is_admin, college)
            VALUES (?, ?, '已认证', 1, '系统管理员')
        ''', ('admin', hashed_password))
    
    db.commit()
    print("数据库初始化完成！")

# ==================== 登录验证装饰器 ====================

def login_required(f):
    """登录验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.is_json:
                return jsonify({'code': 401, 'message': '请先登录'}), 401
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """管理员验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        db = get_db()
        user = db.execute('SELECT is_admin FROM user WHERE id = ?', 
                         (session['user_id'],)).fetchone()
        if not user or user['is_admin'] != 1:
            return render_template('error.html', message='无权限访问')
        return f(*args, **kwargs)
    return decorated_function

def auth_required(f):
    """学生认证验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        db = get_db()
        user = db.execute('SELECT auth_status FROM user WHERE id = ?', 
                         (session['user_id'],)).fetchone()
        if user['auth_status'] != '已认证':
            return render_template('error.html', message='请先完成学生认证后再发布闲置')
        return f(*args, **kwargs)
    return decorated_function

# ==================== 页面路由 ====================

@app.route('/')
def index():
    """首页 - 闲置物品列表"""
    db = get_db()
    
    # 获取筛选参数
    keyword = request.args.get('keyword', '')
    category = request.args.get('category', '')
    
    # 构建查询 - 增加收藏数量
    query = '''
        SELECT item.*, user.username, user.college,
               (SELECT COUNT(*) FROM favorite WHERE favorite.item_id = item.id) as favorite_count
        FROM item 
        JOIN user ON item.user_id = user.id 
        WHERE item.status = '在售'
    '''
    params = []
    
    if keyword:
        query += ' AND (item.title LIKE ? OR item.description LIKE ?)'
        params.extend([f'%{keyword}%', f'%{keyword}%'])
    
    if category:
        query += ' AND item.category = ?'
        params.append(category)
    
    query += ' ORDER BY item.created_at DESC'
    
    items = db.execute(query, params).fetchall()
    categories = db.execute('SELECT DISTINCT category FROM item').fetchall()
    
    # 检查当前用户是否收藏了每个物品
    user_favorites = set()
    if 'user_id' in session:
        favorites = db.execute(
            'SELECT item_id FROM favorite WHERE user_id = ?', 
            (session['user_id'],)
        ).fetchall()
        user_favorites = {f['item_id'] for f in favorites}
    
    return render_template('index.html', items=items, categories=categories, 
                          keyword=keyword, selected_category=category,
                          user_favorites=user_favorites)

@app.route('/item/<int:item_id>')
def item_detail(item_id):
    """物品详情页"""
    db = get_db()
    item = db.execute('''
        SELECT item.*, user.username, user.college, user.phone, user.email
        FROM item 
        JOIN user ON item.user_id = user.id 
        WHERE item.id = ?
    ''', (item_id,)).fetchone()
    
    if not item:
        return render_template('error.html', message='物品不存在')
    
    # 记录浏览历史（如果已登录）
    if 'user_id' in session:
        # 先删除旧记录避免重复
        db.execute('DELETE FROM browse_history WHERE user_id = ? AND item_id = ?',
                   (session['user_id'], item_id))
        # 添加新记录
        db.execute('INSERT INTO browse_history (user_id, item_id) VALUES (?, ?)',
                   (session['user_id'], item_id))
        db.commit()
        
        # 检查是否已收藏
        is_favorited = db.execute(
            'SELECT id FROM favorite WHERE user_id = ? AND item_id = ?',
            (session['user_id'], item_id)
        ).fetchone() is not None
    else:
        is_favorited = False
    
    # 获取留言列表
    comments = db.execute('''
        SELECT c.*, u.username 
        FROM comment c 
        JOIN user u ON c.user_id = u.id 
        WHERE c.item_id = ? AND c.reply_to IS NULL
        ORDER BY c.created_at DESC
    ''', (item_id,)).fetchall()
    
    # 获取每个留言的回复
    comment_replies = {}
    for comment in comments:
        replies = db.execute('''
            SELECT c.*, u.username 
            FROM comment c 
            JOIN user u ON c.user_id = u.id 
            WHERE c.reply_to = ?
            ORDER BY c.created_at ASC
        ''', (comment['id'],)).fetchall()
        comment_replies[comment['id']] = replies
    
    return render_template('item_detail.html', item=item, 
                          is_favorited=is_favorited,
                          comments=comments,
                          comment_replies=comment_replies)

# -------------------- 登录注册 --------------------

@app.route('/login', methods=['GET', 'POST'])
def login():
    """登录页面"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        if not username or not password:
            return render_template('login.html', error='请填写用户名和密码')
        
        db = get_db()
        user = db.execute('SELECT * FROM user WHERE username = ?', (username,)).fetchone()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='用户名或密码错误')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """注册页面"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()
        
        # 验证
        if not username or not password:
            return render_template('register.html', error='用户名和密码不能为空')
        
        if len(username) < 3:
            return render_template('register.html', error='用户名至少3个字符')
        
        if len(password) < 6:
            return render_template('register.html', error='密码至少6个字符')
        
        if password != confirm_password:
            return render_template('register.html', error='两次密码不一致')
        
        db = get_db()
        
        # 检查用户名是否存在
        if db.execute('SELECT id FROM user WHERE username = ?', (username,)).fetchone():
            return render_template('register.html', error='用户名已存在')
        
        # 创建用户
        hashed_password = generate_password_hash(password)
        db.execute('''
            INSERT INTO user (username, password, phone, email)
            VALUES (?, ?, ?, ?)
        ''', (username, hashed_password, phone, email))
        db.commit()
        
        return redirect(url_for('login', success='注册成功，请登录'))
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    """退出登录"""
    session.clear()
    return redirect(url_for('index'))

# -------------------- 个人中心 --------------------

@app.route('/profile')
@login_required
def profile():
    """个人中心"""
    db = get_db()
    user = db.execute('SELECT * FROM user WHERE id = ?', (session['user_id'],)).fetchone()
    my_items = db.execute('''
        SELECT * FROM item WHERE user_id = ? ORDER BY created_at DESC
    ''', (session['user_id'],)).fetchall()
    
    return render_template('profile.html', user=user, my_items=my_items)

@app.route('/auth', methods=['GET', 'POST'])
@login_required
def student_auth():
    """学生认证页面"""
    db = get_db()
    user = db.execute('SELECT * FROM user WHERE id = ?', (session['user_id'],)).fetchone()
    
    if request.method == 'POST':
        student_id = request.form.get('student_id', '').strip()
        college = request.form.get('college', '').strip()
        student_card_url = request.form.get('student_card_url', '').strip()
        
        if not student_id or not college or not student_card_url:
            return render_template('auth.html', user=user, error='请填写完整信息')
        
        # 更新认证信息
        db.execute('''
            UPDATE user SET student_id = ?, college = ?, student_card_url = ?, auth_status = '待审核'
            WHERE id = ?
        ''', (student_id, college, student_card_url, session['user_id']))
        db.commit()
        
        return redirect(url_for('profile'))
    
    return render_template('auth.html', user=user)

# -------------------- 发布闲置 --------------------

@app.route('/publish', methods=['GET', 'POST'])
@login_required
@auth_required
def publish():
    """发布闲置物品"""
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        category = request.form.get('category', '').strip()
        condition = request.form.get('condition', '9成新').strip()
        price = request.form.get('price', '0').strip()
        image_url = request.form.get('image_url', '').strip()
        contact = request.form.get('contact', '').strip()
        description = request.form.get('description', '').strip()
        
        if not title:
            return render_template('publish.html', error='请填写物品名称')
        
        try:
            price = float(price)
        except:
            price = 0
        
        db = get_db()
        db.execute('''
            INSERT INTO item (title, category, condition, price, image_url, contact, description, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (title, category, condition, price, image_url, contact, description, session['user_id']))
        db.commit()
        
        return redirect(url_for('index'))
    
    return render_template('publish.html')

@app.route('/item/<int:item_id>/delete', methods=['POST'])
@login_required
def delete_item(item_id):
    """删除物品"""
    db = get_db()
    item = db.execute('SELECT * FROM item WHERE id = ?', (item_id,)).fetchone()
    
    if not item:
        return render_template('error.html', message='物品不存在')
    
    if item['user_id'] != session['user_id']:
        return render_template('error.html', message='无权限删除')
    
    db.execute('DELETE FROM item WHERE id = ?', (item_id,))
    db.commit()
    
    return redirect(url_for('profile'))

@app.route('/item/<int:item_id>/sold', methods=['POST'])
@login_required
def mark_sold(item_id):
    """标记已售"""
    db = get_db()
    item = db.execute('SELECT * FROM item WHERE id = ?', (item_id,)).fetchone()
    
    if not item or item['user_id'] != session['user_id']:
        return render_template('error.html', message='无权限操作')
    
    db.execute('UPDATE item SET status = ? WHERE id = ?', ('已售', item_id))
    db.commit()
    
    return redirect(url_for('profile'))

# -------------------- 管理员后台 --------------------

@app.route('/admin')
@admin_required
def admin():
    """管理员后台首页"""
    db = get_db()
    
    # 统计数据
    total_users = db.execute('SELECT COUNT(*) as count FROM user').fetchone()['count']
    total_items = db.execute('SELECT COUNT(*) as count FROM item').fetchone()['count']
    pending_auth = db.execute(
        "SELECT COUNT(*) as count FROM user WHERE auth_status = '待审核'"
    ).fetchone()['count']
    
    # 待审核认证列表
    auth_list = db.execute('''
        SELECT id, username, student_id, college, student_card_url, created_at 
        FROM user WHERE auth_status = '待审核' ORDER BY created_at DESC
    ''').fetchall()
    
    return render_template('admin.html', 
                          total_users=total_users,
                          total_items=total_items,
                          pending_auth=pending_auth,
                          auth_list=auth_list)

@app.route('/admin/auth/<int:user_id>/<action>')
@admin_required
def admin_auth_action(user_id, action):
    """管理员审核认证"""
    if action not in ['approve', 'reject']:
        return render_template('error.html', message='无效操作')
    
    db = get_db()
    status = '已认证' if action == 'approve' else '未认证'
    db.execute('UPDATE user SET auth_status = ? WHERE id = ?', (status, user_id))
    db.commit()
    
    return redirect(url_for('admin'))

@app.route('/admin/users')
@admin_required
def admin_users():
    """用户列表"""
    db = get_db()
    users = db.execute('SELECT * FROM user ORDER BY created_at DESC').fetchall()
    return render_template('admin_users.html', users=users)

@app.route('/admin/items')
@admin_required
def admin_items():
    """物品列表"""
    db = get_db()
    items = db.execute('''
        SELECT item.*, user.username FROM item 
        JOIN user ON item.user_id = user.id 
        ORDER BY item.created_at DESC
    ''').fetchall()
    return render_template('admin_items.html', items=items)

# -------------------- 收藏功能 --------------------

@app.route('/favorite/<int:item_id>', methods=['POST'])
@login_required
def toggle_favorite(item_id):
    """添加/取消收藏"""
    db = get_db()
    
    # 检查物品是否存在
    item = db.execute('SELECT id FROM item WHERE id = ?', (item_id,)).fetchone()
    if not item:
        if request.is_json:
            return jsonify({'code': 404, 'message': '物品不存在'}), 404
        return render_template('error.html', message='物品不存在')
    
    # 检查是否已收藏
    existing = db.execute(
        'SELECT id FROM favorite WHERE user_id = ? AND item_id = ?',
        (session['user_id'], item_id)
    ).fetchone()
    
    if existing:
        # 取消收藏
        db.execute('DELETE FROM favorite WHERE user_id = ? AND item_id = ?',
                  (session['user_id'], item_id))
        db.commit()
        favorited = False
        message = '已取消收藏'
    else:
        # 添加收藏
        db.execute('INSERT INTO favorite (user_id, item_id) VALUES (?, ?)',
                  (session['user_id'], item_id))
        db.commit()
        favorited = True
        message = '已添加收藏'
    
    if request.is_json:
        return jsonify({'code': 200, 'message': message, 'favorited': favorited})
    
    # 非JSON请求，返回来源页面
    return redirect(request.referrer or url_for('index'))

@app.route('/my/favorites')
@login_required
def my_favorites():
    """我的收藏"""
    db = get_db()
    favorites = db.execute('''
        SELECT f.*, i.*, u.username, u.college,
               (SELECT COUNT(*) FROM favorite WHERE favorite.item_id = i.id) as favorite_count
        FROM favorite f
        JOIN item i ON f.item_id = i.id
        JOIN user u ON i.user_id = u.id
        WHERE f.user_id = ?
        ORDER BY f.created_at DESC
    ''', (session['user_id'],)).fetchall()
    
    return render_template('favorites.html', favorites=favorites)

# -------------------- 浏览历史 --------------------

@app.route('/my/history')
@login_required
def my_history():
    """浏览历史"""
    db = get_db()
    history = db.execute('''
        SELECT h.*, i.*, u.username, u.college,
               (SELECT COUNT(*) FROM favorite WHERE favorite.item_id = i.id) as favorite_count
        FROM browse_history h
        JOIN item i ON h.item_id = i.id
        JOIN user u ON i.user_id = u.id
        WHERE h.user_id = ?
        ORDER BY h.created_at DESC
        LIMIT 100
    ''', (session['user_id'],)).fetchall()
    
    return render_template('history.html', history=history)

@app.route('/my/history/clear', methods=['POST'])
@login_required
def clear_history():
    """清空浏览历史"""
    db = get_db()
    db.execute('DELETE FROM browse_history WHERE user_id = ?', (session['user_id'],))
    db.commit()
    
    if request.is_json:
        return jsonify({'code': 200, 'message': '浏览历史已清空'})
    
    return redirect(url_for('my_history'))

# -------------------- 留言功能 --------------------

@app.route('/comment/<int:item_id>', methods=['POST'])
@login_required
def add_comment(item_id):
    """添加留言"""
    content = request.form.get('content', '').strip() or (request.get_json().get('content', '').strip() if request.is_json else '')
    
    if not content:
        if request.is_json:
            return jsonify({'code': 400, 'message': '留言内容不能为空'}), 400
        return render_template('error.html', message='留言内容不能为空')
    
    db = get_db()
    
    # 检查物品是否存在
    item = db.execute('SELECT id FROM item WHERE id = ?', (item_id,)).fetchone()
    if not item:
        if request.is_json:
            return jsonify({'code': 404, 'message': '物品不存在'}), 404
        return render_template('error.html', message='物品不存在')
    
    # 添加留言
    db.execute('''
        INSERT INTO comment (item_id, user_id, content)
        VALUES (?, ?, ?)
    ''', (item_id, session['user_id'], content))
    db.commit()
    
    if request.is_json:
        return jsonify({'code': 200, 'message': '留言成功'})
    
    return redirect(url_for('item_detail', item_id=item_id))

@app.route('/comment/<int:comment_id>/reply', methods=['POST'])
@login_required
def reply_comment(comment_id):
    """回复留言"""
    content = request.form.get('content', '').strip() or (request.get_json().get('content', '').strip() if request.is_json else '')
    
    if not content:
        if request.is_json:
            return jsonify({'code': 400, 'message': '回复内容不能为空'}), 400
        return render_template('error.html', message='回复内容不能为空')
    
    db = get_db()
    
    # 检查原留言是否存在
    parent_comment = db.execute('SELECT id, item_id FROM comment WHERE id = ?', (comment_id,)).fetchone()
    if not parent_comment:
        if request.is_json:
            return jsonify({'code': 404, 'message': '原留言不存在'}), 404
        return render_template('error.html', message='原留言不存在')
    
    # 添加回复
    db.execute('''
        INSERT INTO comment (item_id, user_id, content, reply_to)
        VALUES (?, ?, ?, ?)
    ''', (parent_comment['item_id'], session['user_id'], content, comment_id))
    db.commit()
    
    if request.is_json:
        return jsonify({'code': 200, 'message': '回复成功'})
    
    return redirect(url_for('item_detail', item_id=parent_comment['item_id']))

# ==================== API接口 ====================

@app.route('/api/items', methods=['GET'])
def api_get_items():
    """获取闲置物品列表API"""
    db = get_db()
    keyword = request.args.get('keyword', '')
    category = request.args.get('category', '')
    
    query = '''
        SELECT item.*, user.username, user.college 
        FROM item JOIN user ON item.user_id = user.id 
        WHERE item.status = '在售'
    '''
    params = []
    
    if keyword:
        query += ' AND (item.title LIKE ? OR item.description LIKE ?)'
        params.extend([f'%{keyword}%', f'%{keyword}%'])
    
    if category:
        query += ' AND item.category = ?'
        params.append(category)
    
    query += ' ORDER BY item.created_at DESC'
    
    items = db.execute(query, params).fetchall()
    
    return jsonify({
        'code': 200,
        'message': 'success',
        'data': [dict(item) for item in items]
    })

@app.route('/api/items', methods=['POST'])
@login_required
def api_create_item():
    """发布闲置物品API"""
    data = request.get_json()
    
    db = get_db()
    user = db.execute('SELECT auth_status FROM user WHERE id = ?', 
                     (session['user_id'],)).fetchone()
    
    if user['auth_status'] != '已认证':
        return jsonify({'code': 403, 'message': '请先完成学生认证'}), 403
    
    db.execute('''
        INSERT INTO item (title, category, price, image_url, contact, description, user_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        data.get('title'),
        data.get('category'),
        data.get('price', 0),
        data.get('image_url'),
        data.get('contact'),
        data.get('description'),
        session['user_id']
    ))
    db.commit()
    
    return jsonify({'code': 200, 'message': '发布成功'})

@app.route('/api/user/login', methods=['POST'])
def api_login():
    """登录API"""
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    
    if not username or not password:
        return jsonify({'code': 400, 'message': '请填写用户名和密码'}), 400
    
    db = get_db()
    user = db.execute('SELECT * FROM user WHERE username = ?', (username,)).fetchone()
    
    if user and check_password_hash(user['password'], password):
        session['user_id'] = user['id']
        session['username'] = user['username']
        return jsonify({
            'code': 200,
            'message': '登录成功',
            'data': {
                'id': user['id'],
                'username': user['username'],
                'is_admin': user['is_admin']
            }
        })
    
    return jsonify({'code': 401, 'message': '用户名或密码错误'}), 401

@app.route('/api/user/register', methods=['POST'])
def api_register():
    """注册API"""
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    phone = data.get('phone', '').strip()
    email = data.get('email', '').strip()
    
    if not username or not password:
        return jsonify({'code': 400, 'message': '用户名和密码不能为空'}), 400
    
    if len(username) < 3:
        return jsonify({'code': 400, 'message': '用户名至少3个字符'}), 400
    
    if len(password) < 6:
        return jsonify({'code': 400, 'message': '密码至少6个字符'}), 400
    
    db = get_db()
    
    if db.execute('SELECT id FROM user WHERE username = ?', (username,)).fetchone():
        return jsonify({'code': 400, 'message': '用户名已存在'}), 400
    
    hashed_password = generate_password_hash(password)
    db.execute('''
        INSERT INTO user (username, password, phone, email)
        VALUES (?, ?, ?, ?)
    ''', (username, hashed_password, phone, email))
    db.commit()
    
    return jsonify({'code': 200, 'message': '注册成功'})

@app.route('/api/user/info')
@login_required
def api_user_info():
    """获取用户信息API"""
    db = get_db()
    user = db.execute('SELECT id, username, phone, email, auth_status, student_id, college, is_admin FROM user WHERE id = ?', 
                     (session['user_id'],)).fetchone()
    
    return jsonify({
        'code': 200,
        'data': dict(user) if user else None
    })

@app.route('/api/user/auth', methods=['POST'])
@login_required
def api_student_auth():
    """学生认证API"""
    data = request.get_json()
    student_id = data.get('student_id', '').strip()
    college = data.get('college', '').strip()
    student_card_url = data.get('student_card_url', '').strip()
    
    if not student_id or not college or not student_card_url:
        return jsonify({'code': 400, 'message': '请填写完整信息'}), 400
    
    db = get_db()
    db.execute('''
        UPDATE user SET student_id = ?, college = ?, student_card_url = ?, auth_status = '待审核'
        WHERE id = ?
    ''', (student_id, college, student_card_url, session['user_id']))
    db.commit()
    
    return jsonify({'code': 200, 'message': '认证申请已提交'})

# ==================== 健康检查 ====================

@app.route('/health')
def health():
    """健康检查端点 - 用于 Render 探活"""
    return jsonify({'status': 'ok', 'service': 'hnau-market'})

# ==================== 启动应用 ====================

if __name__ == '__main__':
    # 确保数据库目录存在
    os.makedirs(os.path.dirname(DATABASE_PATH) if os.path.dirname(DATABASE_PATH) else '/tmp', exist_ok=True)
    
    # 初始化数据库
    with app.app_context():
        init_db()
    
    # Render 会自动设置 PORT 环境变量
    # 本地开发使用默认端口 5000
    app.run(host='0.0.0.0', port=PORT, debug=False)
