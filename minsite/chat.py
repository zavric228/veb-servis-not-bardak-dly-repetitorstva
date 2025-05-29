from flask import Blueprint, session, request, jsonify, abort
from flask_socketio import emit
import os
import time
from database import get_db

chat_bp = Blueprint('chat', __name__)

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

def register_socket_handlers(socketio):
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