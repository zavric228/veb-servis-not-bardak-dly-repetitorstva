from flask import Flask, redirect, url_for, session, render_template, request, flash, abort, g, Blueprint
from flask_socketio import SocketIO, emit
import os
import time

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config.update(
    UPLOAD_FOLDER_PROFILE='static/img/avatars',
    UPLOAD_FOLDER_ACHIEVEMENTS='static/img/achievements',
    UPLOAD_FOLDER_STUDENTS_ACHIEVEMENTS='static/img/students_achievements',
    DATABASE='database.db',
    ALLOWED_EXTENSIONS={'png', 'jpg', 'jpeg'},
    MAX_CONTENT_LENGTH=20 * 1024 * 1024,
    TEMPLATES_AUTO_RELOAD=True
)

socketio = SocketIO(app, cors_allowed_origins="*")

# Регистрация Blueprint
from auth import auth_bp
from profile import profile_bp
from achievements import achievements_bp

app.register_blueprint(auth_bp)
app.register_blueprint(profile_bp)
app.register_blueprint(achievements_bp)

@app.route('/student_profile')
def student_profile():
    db = get_db()
    
    if is_student:
        if 'user' not in session:
            return redirect(url_for('auth.login'))
        
        student = db.execute('SELECT * FROM students WHERE username = ?', (session['user'],)).fetchone()
        if not student:
            db.execute('INSERT INTO students (username) VALUES (?)', (session['user'],))
            db.commit()
            student = db.execute('SELECT * FROM students WHERE username = ?', (session['user'],)).fetchone()
        
        profile = dict(student)
        profile_photo_path = f'img/avatars/{student["photo"]}'
        default_photo = url_for('static', filename='img/avatars/nkvtf.jpg')
        
        # Достижения ученика
        achievements = db.execute('''
            SELECT * FROM achievements 
            WHERE student_id = ?
        ''', (student['id'],)).fetchall()
        
        # Сообщения для чата
        messages = db.execute('''
            SELECT * FROM messages 
            WHERE (sender = ? AND receiver = 'zavric228')
            OR (sender = 'zavric228' AND receiver = ?)
            ORDER BY timestamp ASC
        ''', (session['user'], session['user'])).fetchall()
        
        return render_template('index.html',
            profile=profile,
            profile_title='Профиль ученика',
            profile_photo_path=profile_photo_path,
            default_photo=default_photo,
            achievements=achievements,
            messages=messages,
            is_admin=session.get('is_admin', False),
            logged_in='user' in session,
            is_student_profile=True
        )
    else:
        profile_data = db.execute('SELECT * FROM profile WHERE user_id = 1').fetchone()
        profile = dict(profile_data) if profile_data else {}
        profile_photo_path = f'img/avatars/{profile.get("photo", "default.jpg")}'
        default_photo = url_for('static', filename='img/avatars/default.jpg')
        
        achievements = db.execute('SELECT * FROM achievements WHERE is_student = 0').fetchall()
        student_achievements = db.execute('''
            SELECT a.*, s.username as student_name 
            FROM achievements a
            LEFT JOIN students s ON a.student_id = s.id
            WHERE a.is_student = 1
        ''').fetchall()
        
        return render_template('index.html',
            profile=profile,
            title='Профиль преподавателя',
            profile_photo_path=profile_photo_path,
            default_photo=default_photo,
            achievements=achievements,
            student_achievements=student_achievements,
            is_admin=session.get('is_admin', False),
            logged_in='user' in session,
            is_student_profile=False
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
        os.makedirs('static/chat_files', exist_ok=True)
        
        # Конвертируем список обратно в bytes
        file_data = bytes(bytearray(data['file']['data']))
        with open(filepath, 'wb') as f:
            f.write(file_data)
        
        file_url = f"/static/chat_files/{filename}"

    db = get_db()
    text = data.get('text', '')
    
    # Определяем получателя
    receiver = 'zavric228' if not session.get('is_admin') else data.get('receiver')
    
    db.execute('INSERT INTO messages (sender, receiver, text, file) VALUES (?, ?, ?, ?)', 
              (session['user'], receiver, text, file_url))
    db.commit()

    emit('new_message', {
        'text': text,
        'file': file_url,
        'sender': session['user'],
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
    }, room=f"user_{receiver}")

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER_PROFILE'], exist_ok=True)
    os.makedirs(app.config['UPLOAD_FOLDER_ACHIEVEMENTS'], exist_ok=True)
    os.makedirs(app.config['UPLOAD_FOLDER_STUDENTS_ACHIEVEMENTS'], exist_ok=True)
    os.makedirs('static/chat_files', exist_ok=True)
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)