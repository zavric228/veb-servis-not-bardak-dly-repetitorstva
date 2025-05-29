# Импорт библиотек

from flask import Flask, render_template, request, redirect, url_for, flash, session, abort, jsonify, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_socketio import SocketIO, emit
import os
import sqlite3
import logging
import time
from datetime import datetime

# Конфигурация приложения

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = 'SECRET_KEY_123'
app.config['UPLOAD_FOLDER_PROFILE'] = 'static/img/profile'
app.config['UPLOAD_FOLDER_ACHIEVEMENTS'] = 'static/img/achievements'
app.config['UPLOAD_FOLDER_STUDENTS_ACHIEVEMENTS'] = 'static/img/students_achievements'
app.config['DATABASE'] = 'database.db'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg'}
app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024  # 20 MB

socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Работа с базой данных

def get_db():
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def init_db():
    try:
        with get_db() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT,
                    is_admin BOOLEAN DEFAULT 0
                );
                
                CREATE TABLE IF NOT EXISTS profile (
                    user_id INTEGER PRIMARY KEY,
                    name TEXT DEFAULT '',
                    phone TEXT DEFAULT '',
                    email TEXT DEFAULT '',
                    telegram TEXT DEFAULT '',
                    photo TEXT DEFAULT 'nkvtf.jpg'
                );
                
                CREATE TABLE IF NOT EXISTS achievements (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER,
                    image TEXT NOT NULL,
                    description TEXT NOT NULL,
                    is_student BOOLEAN DEFAULT 0,
                    student_id INTEGER
                );
                
                CREATE TABLE IF NOT EXISTS students (
                    id INTEGER PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    photo TEXT DEFAULT 'nkvtf.jpg',
                    name TEXT DEFAULT '',
                    level TEXT DEFAULT ''
                );
                
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY,
                    sender TEXT NOT NULL,
                    text TEXT NOT NULL,
                    file TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                );
            ''')

            admin_password = generate_password_hash('12345679')
            db.execute('''
                INSERT OR IGNORE INTO users (username, password, is_admin)
                VALUES (?, ?, 1)
            ''', ('zavric228', admin_password))
            db.execute('INSERT OR IGNORE INTO profile (user_id) VALUES (1)')
            
        logger.info("База данных инициализирована")
    except Exception as e:
        logger.error(f"Ошибка инициализации БД: {str(e)}")
        raise

# Инициализация приложения
@app.before_first_request
def startup():
    try:
        os.makedirs(app.config['UPLOAD_FOLDER_PROFILE'], exist_ok=True)
        os.makedirs(app.config['UPLOAD_FOLDER_ACHIEVEMENTS'], exist_ok=True)
        os.makedirs(app.config['UPLOAD_FOLDER_STUDENTS_ACHIEVEMENTS'], exist_ok=True)
        os.makedirs('static/chat_files', exist_ok=True)
        init_db()
    except Exception as e:
        logger.critical(f"Ошибка запуска: {str(e)}")

# Маршруты приложения
@app.route('/')
def index():
    try:
        with get_db() as db:
            profile = db.execute('SELECT * FROM profile WHERE user_id = 1').fetchone()
            achievements = db.execute('''
                SELECT a.*, s.username as student_name 
                FROM achievements a
                LEFT JOIN students s ON a.student_id = s.id
                WHERE a.user_id = 1 AND a.is_student = 0
            ''').fetchall()
            
            student_achievements = db.execute('''
                SELECT a.*, s.username as student_name 
                FROM achievements a
                LEFT JOIN students s ON a.student_id = s.id
                WHERE a.is_student = 1
            ''').fetchall()
        
        return render_template('index.html',
                            profile=dict(profile) if profile else {},
                            achievements=achievements,
                            student_achievements=student_achievements,
                            is_admin=session.get('user', {}).get('is_admin', False))
    except Exception as e:
        logger.error(f"Ошибка в index(): {str(e)}")
        return render_template('error.html', error="Ошибка загрузки данных"), 500

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form.get('password')
        
        with get_db() as db:
            user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
            
            if username == 'zavric228':
                if not user or not check_password_hash(user['password'], password):
                    flash('Неверный пароль', 'error')
                    return render_template('auth/login.html', ask_password=True)
            elif not user:
                flash('Пользователь не найден', 'error')
                return redirect(url_for('login'))
            
            session['user'] = {
                'username': username,
                'is_admin': username == 'zavric228'
            }
            return redirect(url_for('index'))
    
    ask_password = request.args.get('ask_password', False)
    return render_template('auth/login.html', ask_password=ask_password)

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        if len(username) > 100:
            flash('Логин слишком длинный (максимум 100 символов)', 'error')
            return redirect(url_for('register'))
        
        try:
            with get_db() as db:
                db.execute('INSERT INTO users (username) VALUES (?)', (username,))
                db.execute('INSERT INTO students (username) VALUES (?)', (username,))
                db.commit()
            
            session['user'] = {'username': username, 'is_admin': False}
            flash('Регистрация успешна', 'success')
            return redirect(url_for('index'))
        except sqlite3.IntegrityError:
            flash('Этот логин уже занят', 'error')
    
    return render_template('auth/register.html')

@app.route('/student_profile')
def student_profile():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    with get_db() as db:
        student = db.execute('''
            SELECT * FROM students 
            WHERE username = ?
        ''', (session['user']['username'],)).fetchone()
        
        if not student:
            student = {
                'username': session['user']['username'],
                'photo': 'nkvtf.jpg',
                'name': '',
                'level': ''
            }
            db.execute('''
                INSERT INTO students (username, photo)
                VALUES (?, ?)
            ''', (student['username'], student['photo']))
            db.commit()
        
        messages = db.execute('''
            SELECT * FROM messages 
            WHERE sender = ? OR sender = 'tutor'
            ORDER BY timestamp
        ''', (session['user']['username'],)).fetchall()
    
    return render_template('sections/student_profile.html',
                         student=dict(student),
                         messages=messages)
@app.route('/update_profile', methods=['POST'])
def update_profile():
    if not session.get('user') or not session['user']['is_admin']:
        abort(403, description="Доступ запрещён")
    
    name = request.form['name']
    phone = request.form['phone']
    email = request.form['email']
    telegram = request.form['telegram']
    
    with get_db() as db:
        db.execute('''
            INSERT OR REPLACE INTO profile 
            (user_id, name, phone, email, telegram) 
            VALUES (1, ?, ?, ?, ?)
        ''', (name, phone, email, telegram))
        
        if 'photo' in request.files:
            photo = request.files['photo']
            if photo.filename != '' and allowed_file(photo.filename):
                filename = secure_filename(photo.filename)
                photo.save(os.path.join(app.config['UPLOAD_FOLDER_PROFILE'], filename))
                db.execute('UPDATE profile SET photo = ? WHERE user_id = 1', (filename,))
        
        db.commit()
    
    flash('Профиль обновлён', 'success')
    return redirect(url_for('index'))

@app.route('/add_achievement', methods=['POST'])
def add_achievement():
    if not session.get('user') or not session['user']['is_admin']:
        abort(403, description="Доступ запрещён")
    
    description = request.form['description']
    is_student = 1 if 'is_student' in request.form else 0
    student_id = request.form.get('student_id')
    
    if 'image' not in request.files:
        flash('Выберите файл', 'error')
        return redirect(url_for('index'))
    
    file = request.files['image']
    if file.filename == '' or not allowed_file(file.filename):
        flash('Допустимы только PNG, JPG, JPEG', 'error')
        return redirect(url_for('index'))
    
    filename = secure_filename(file.filename)
    folder = app.config['UPLOAD_FOLDER_STUDENTS_ACHIEVEMENTS'] if is_student else app.config['UPLOAD_FOLDER_ACHIEVEMENTS']
    file.save(os.path.join(folder, filename))
    
    with get_db() as db:
        db.execute('''
            INSERT INTO achievements 
            (user_id, image, description, is_student, student_id) 
            VALUES (1, ?, ?, ?, ?)
        ''', (filename, description, is_student, student_id))
        db.commit()
    
    flash('Достижение добавлено', 'success')
    return redirect(url_for('index'))

@app.route('/delete_achievement/<int:id>', methods=['POST'])
def delete_achievement(id):
    if not session.get('user') or not session['user']['is_admin']:
        abort(403, description="Доступ запрещён")
    
    with get_db() as db:
        achievement = db.execute('SELECT * FROM achievements WHERE id = ?', (id,)).fetchone()
        if achievement:
            folder = app.config['UPLOAD_FOLDER_STUDENTS_ACHIEVEMENTS'] if achievement['is_student'] else app.config['UPLOAD_FOLDER_ACHIEVEMENTS']
            try:
                os.remove(os.path.join(folder, achievement['image']))
            except FileNotFoundError:
                pass
            db.execute('DELETE FROM achievements WHERE id = ?', (id,))
            db.commit()
    
    return redirect(url_for('index'))

@app.route('/update_student_profile', methods=['POST'])
def update_student_profile():
    if 'user' not in session:
        abort(403)
    
    student_id = request.form['student_id']
    name = request.form['name']
    level = request.form['level']
    
    with get_db() as db:
        # Проверка прав
        if not session['user']['is_admin']:
            student = db.execute('SELECT username FROM students WHERE id = ?', (student_id,)).fetchone()
            if not student or student['username'] != session['user']['username']:
                abort(403)
        
        # Обновление данных
        update_data = {'name': name, 'level': level}
        if 'photo' in request.files:
            photo = request.files['photo']
            if photo.filename and allowed_file(photo.filename):
                filename = secure_filename(f"{student_id}_{photo.filename}")
                photo.save(os.path.join('static/img/students', filename))
                update_data['photo'] = filename
        
        db.execute('''
            UPDATE students 
            SET name = :name, 
                level = :level, 
                photo = COALESCE(:photo, photo) 
            WHERE id = :id
        ''', {**update_data, 'id': student_id})
        db.commit()
    
    return redirect(url_for('student_profile'))

@app.route('/api/students')
def api_students():
    if not session.get('user') or not session['user']['is_admin']:
        abort(403)
    query = request.args.get('q', '').strip()
    with get_db() as db:
        students = db.execute('''
            SELECT id, username, name 
            FROM students 
            WHERE username LIKE ? OR name LIKE ?
            LIMIT 10
        ''', (f'%{query}%', f'%{query}%')).fetchall()
    return jsonify([dict(row) for row in students])

@app.route('/admin_panel')
def admin_panel():
    if not session.get('user') or not session['user']['is_admin']:
        abort(403)
    
    with get_db() as db:
        all_chats = db.execute('''
            SELECT DISTINCT sender 
            FROM messages 
            WHERE sender != 'tutor'
            ORDER BY timestamp DESC
        ''').fetchall()
        
        students = db.execute('SELECT * FROM students').fetchall()
    
    return render_template('admin_panel.html',
                        active_chats=all_chats,
                        students=students)

@app.route('/admin_chat/<username>')
def admin_chat(username):
    if not session.get('user') or not session['user']['is_admin']:
        abort(403)
    
    with get_db() as db:
        messages = db.execute('''
            SELECT * FROM messages 
            WHERE sender = ? OR sender = 'tutor'
            ORDER BY timestamp
        ''', (username,)).fetchall()
        
        student = db.execute('SELECT * FROM students WHERE username = ?', (username,)).fetchone()
    
    return render_template('admin_chat.html',
                        messages=messages,
                        student=student,
                        current_user=session['user']['username'])
# WebSocket обработчики
@socketio.on('connect')
def handle_connect():
    if 'user' in session:
        emit('user_connected', {'username': session['user']['username']})

@socketio.on('message')
def handle_message(data):
    if 'user' not in session or session['user']['is_admin']:
        return
    
    file_url = None
    if 'file' in data:
        try:
            filename = f"{session['user']['username']}_{int(time.time())}.{data['file']['ext']}"
            filepath = os.path.join('static/chat_files', filename)
            with open(filepath, 'wb') as f:
                f.write(data['file']['data'])
            file_url = f"/static/chat_files/{filename}"
        except Exception as e:
            logger.error(f"Ошибка загрузки файла: {str(e)}")
    
    with get_db() as db:
        db.execute('''
            INSERT INTO messages 
            (sender, text, file) 
            VALUES (?, ?, ?)
        ''', (session['user']['username'], data['text'], file_url))
        db.commit()
    
    emit('new_message', {
        'text': data['text'],
        'file': file_url,
        'sender': session['user']['username'],
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }, broadcast=True)

@socketio.on('admin_message')
def handle_admin_message(data):
    if 'user' not in session or not session['user']['is_admin']:
        return
    
    file_url = None
    if 'file' in data:
        try:
            filename = f"tutor_{int(time.time())}.{data['file']['ext']}"
            filepath = os.path.join('static/chat_files', filename)
            with open(filepath, 'wb') as f:
                f.write(data['file']['data'])
            file_url = f"/static/chat_files/{filename}"
        except Exception as e:
            logger.error(f"Ошибка загрузки файла: {str(e)}")
    
    with get_db() as db:
        db.execute('''
            INSERT INTO messages 
            (sender, text, file, timestamp) 
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ''', ('tutor', data['text'], file_url))
        db.commit()
    
    emit('new_message', {
        'text': data['text'],
        'file': file_url,
        'sender': 'tutor',
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }, broadcast=True)

# Запуск приложения

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)