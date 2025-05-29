
# Импорт библиотек
from flask import Blueprint, session, request, jsonify
from flask_socketio import emit
import os
import sqlite3
import time
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

# Инициализация Blueprint
chat_bp = Blueprint('chat', __name__)

def get_db():
    conn = sqlite3.connect(current_app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn

# WebSocket обработчики
def handle_connect():
    if 'user' in session:
        emit('user_connected', {
            'username': session['user']['username'],
            'is_admin': session['user']['is_admin']
        })

def handle_message(data):
    if 'user' not in session:
        return
    
    # Проверка прав (админ может отвечать как 'tutor')
    sender = 'tutor' if session['user']['is_admin'] else session['user']['username']
    
    file_url = None
    if 'file' in data:
        try:
            ext = data['file']['ext'].lower()
            if ext not in {'png', 'jpg', 'jpeg'}:
                raise ValueError('Invalid file type')
                
            filename = f"{sender}_{int(time.time())}.{ext}"
            filepath = os.path.join('static/chat_files', filename)
            
            with open(filepath, 'wb') as f:
                f.write(data['file']['data'])
            
            file_url = f"/static/chat_files/{filename}"
        except Exception as e:
            print(f"Ошибка загрузки файла: {str(e)}")
            return

    with get_db() as db:
        db.execute('''
            INSERT INTO messages 
            (sender, text, file) 
            VALUES (?, ?, ?)
        ''', (sender, data['text'], file_url))
        db.commit()
    
    emit('new_message', {
        'text': data['text'],
        'file': file_url,
        'sender': sender,
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
    }, broadcast=True)
# HTTP маршруты чата
@chat_bp.route('/admin_chats')
def admin_chats():
    if not session.get('user') or not session['user']['is_admin']:
        abort(403)
    
    with get_db() as db:
        messages = db.execute('''
            SELECT m.*, s.photo as student_photo 
            FROM messages m
            LEFT JOIN students s ON m.sender = s.username
            ORDER BY m.timestamp DESC
        ''').fetchall()
    
    return jsonify([dict(msg) for msg in messages])

# Регистрация обработчиков WebSocket
def register_socket_handlers(socketio):
    socketio.on_event('connect', handle_connect)
    socketio.on_event('message', handle_message)