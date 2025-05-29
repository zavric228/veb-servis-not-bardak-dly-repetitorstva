from flask import Flask, redirect, url_for, session, render_template, request, flash, abort
from flask_socketio import SocketIO, emit
import os
import time
from database import init_db, get_db, allowed_file
from auth import auth_bp
from profile import profile_bp
from chat import chat_bp
from achievements import achievements_bp

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config.update(
    UPLOAD_FOLDER_PROFILE='static/img/profile',
    UPLOAD_FOLDER_ACHIEVEMENTS='static/img/achievements',
    UPLOAD_FOLDER_STUDENTS_ACHIEVEMENTS='static/img/students_achievements',
    DATABASE='database.db',
    ALLOWED_EXTENSIONS={'png', 'jpg', 'jpeg'},
    MAX_CONTENT_LENGTH=20 * 1024 * 1024,
    TEMPLATES_AUTO_RELOAD=True
)

socketio = SocketIO(app, cors_allowed_origins="*")

# Регистрация Blueprint
app.register_blueprint(auth_bp)
app.register_blueprint(profile_bp)
app.register_blueprint(chat_bp)
app.register_blueprint(achievements_bp)

@app.route('/')
def index():
    db = get_db()
    profile = db.execute('SELECT * FROM profile WHERE user_id = 1').fetchone()
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

@app.errorhandler(403)
def forbidden(e):
    return render_template('error.html', error={'code': 403, 'info': 'Доступ запрещен'}), 403

@app.errorhandler(404)
def not_found(e):
    return render_template('error.html', error={'code': 404, 'info': 'Страница не найдена'}), 404

@app.errorhandler(500)
def internal_error(e):
    return render_template('error.html', error={'code': 500, 'info': 'Внутренняя ошибка сервера'}), 500

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
        return
    
    file_url = None
    if 'file' in data:
        filename = f"{session['user']}_{int(time.time())}.{data['file']['ext']}"
        filepath = os.path.join('static/chat_files', filename)
        with open(filepath, 'wb') as f:
            f.write(data['file']['data'])
        file_url = f"/static/chat_files/{filename}"

    db = get_db()
    db.execute('INSERT INTO messages (sender, text, file) VALUES (?, ?, ?)', 
              (session['user'], data['text'], file_url))
    db.commit()

    emit('new_message', {
        'text': data['text'],
        'file': file_url,
        'sender': session['user'],
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
    }, broadcast=True)

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER_PROFILE'], exist_ok=True)
    os.makedirs(app.config['UPLOAD_FOLDER_ACHIEVEMENTS'], exist_ok=True)
    os.makedirs(app.config['UPLOAD_FOLDER_STUDENTS_ACHIEVEMENTS'], exist_ok=True)
    os.makedirs('static/chat_files', exist_ok=True)
    
    if not os.path.exists(app.config['DATABASE']):
        init_db(app)
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)