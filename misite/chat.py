from flask import Blueprint, session, request, jsonify, abort
from flask_socketio import emit
import os
import time


chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/admin_chat/<sring: user_id>')
def admin_chats(user_id):
    if not session.get('user') or not session['user']['is_admin']:
        abort(403)
    

def register_socket_handlers(socketio):
    @socketio.on('connect')
    def handle_connect():
        if 'rol' in session and session['rol']:
            emit('user_connected', {
                'username': session['user'],
            })

    @socketio.on('message')
    def handle_message(data):
        if 'user' not in session:
            return redirect('/')

        db = get_db()
        db.execute('''
            INSERT INTO messages (sender, text)
            VALUES (?, ?)
        ''', (session['user'], data['text']))
        db.commit()

        emit('new_message', {
            'text': data['text'],
            'sender': session['user'],
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }, broadcast=True)