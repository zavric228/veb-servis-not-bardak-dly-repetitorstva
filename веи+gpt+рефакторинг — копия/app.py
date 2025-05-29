# Импорт библиотек
from flask import Flask, redirect, url_for, session, render_template, request, flash, abort
from flask_socketio import SocketIO, emit
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import sqlite3
import os
import logging
import time

# Конфигурация приложения
app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config.update(
    UPLOAD_FOLDER_PROFILE='static/img/profile',
    UPLOAD_FOLDER_ACHIEVEMENTS='static/img/achievements',
    UPLOAD_FOLDER_STUDENTS_ACHIEVEMENTS='static/img/students_achievements',
    DATABASE='database.db',
    ALLOWED_EXTENSIONS={'png', 'jpg', 'jpeg'},
    MAX_CONTENT_LENGTH=20 * 1024 * 1024,  # 20 MB
    TEMPLATES_AUTO_RELOAD=True
)

# Инициализация SocketIO
socketio = SocketIO(app, cors_allowed_origins="*")

# Регистрация Blueprint
from profile_handlers import profile_bp
app.register_blueprint(profile_bp)

# Вспомогательные функции
def get_db():
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Инициализация БД
def init_db():
    try:
        with app.app_context():
            db = get_db()
            cursor = db.cursor()
            
            # Создание таблиц
            cursor.executescript('''
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
                
                CREATE TABLE IF NOT EXISTS students (
                    id INTEGER PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    photo TEXT DEFAULT 'nkvtf.jpg',
                    name TEXT DEFAULT '',
                    class_is TEXT DEFAULT ''
                );
                
                CREATE TABLE IF NOT EXISTS achievements (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER,
                    image TEXT NOT NULL,
                    description TEXT NOT NULL,
                    is_student BOOLEAN DEFAULT 0,
                    student_id INTEGER
                );
                
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY,
                    sender TEXT NOT NULL,
                    text TEXT NOT NULL,
                    file TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                );
            ''')
            
            # Добавление администратора
            admin_password = generate_password_hash('12345679')
            cursor.execute('''
                INSERT OR IGNORE INTO users (username, password, is_admin)
                VALUES (?, ?, 1)
            ''', ('zavric228', admin_password))
            
            cursor.execute('INSERT OR IGNORE INTO profile (user_id) VALUES (1)')
            db.commit()
    except Exception as e:
        logging.error(f"Ошибка инициализации БД: {str(e)}")
        raise

# Маршруты
@app.route('/')
def index():
    try:
        db = get_db()
        profile = db.execute('SELECT * FROM profile WHERE user_id = 1').fetchall()
        achievements = db.execute('SELECT * FROM achievements WHERE is_student = 0').fetchall()
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
            is_admin=session.get('is_admin', False),
            logged_in='user' in session
        )
    except Exception as e:
        logging.error(f"Ошибка в index(): {str(e)}")
        return render_template('error.html', error="Ошибка загрузки данных"), 500

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form.get('password', '')
        
        try:
            db = get_db()
            user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
            
            if user and check_password_hash(user['password'], password):
                session['user'] = user['username']
                session['is_admin'] = bool(user['is_admin'])
                return redirect(url_for('index'))
            
            flash('Неверные учетные данные', 'error')
        except Exception as e:
            logging.error(f"Ошибка входа: {str(e)}")
            flash('Ошибка сервера', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# Обработчики ошибок
@app.errorhandler(403)
def forbidden(e):
    return render_template('error.html', error={'code': 403, 'description': 'Доступ запрещен'}), 403

@app.errorhandler(404)
def not_found(e):
    return render_template('error.html', error={'code': 404, 'description': 'Страница не найдена'}), 404

@app.errorhandler(500)
def internal_error(e):
    return render_template('error.html', error={'code': 500, 'description': 'Внутренняя ошибка сервера'}), 500

# WebSocket обработчики
@socketio.on('connect')
def handle_connect():
    if 'user' in session:
        emit('user_connected', {
            'username': session['user'],
            'is_admin': session.get('is_admin', False)
        })

@socketio.on('message')
def handle_message(data):
    if 'user' not in session:
        return abort(401)
    
    try:
        file_url = None
        if 'file' in data:
            filename = f"{session['user']}_{int(time.time())}.{data['file']['ext']}"
            filepath = os.path.join('static/chat_files', filename)
            with open(filepath, 'wb') as f:
                f.write(data['file']['data'])
            file_url = f"/static/chat_files/{filename}"

        db = get_db()
        db.execute('''
            INSERT INTO messages (sender, text, file)
            VALUES (?, ?, ?)
        ''', (session['user'], data['text'], file_url))
        db.commit()

        emit('new_message', {
            'text': data['text'],
            'file': file_url,
            'sender': session['user'],
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }, broadcast=True)
    except Exception as e:
        logging.error(f"Ошибка обработки сообщения: {str(e)}")

# Запуск приложения
if __name__ == '__main__':
    # Создание директорий
    os.makedirs(app.config['UPLOAD_FOLDER_PROFILE'], exist_ok=True)
    os.makedirs(app.config['UPLOAD_FOLDER_ACHIEVEMENTS'], exist_ok=True)
    os.makedirs(app.config['UPLOAD_FOLDER_STUDENTS_ACHIEVEMENTS'], exist_ok=True)
    os.makedirs('static/chat_files', exist_ok=True)
    
    # Инициализация БД
    if not os.path.exists(app.config['DATABASE']):
        init_db()

if __name__ == '__main__':
    app.run(debug=True, port=8080)