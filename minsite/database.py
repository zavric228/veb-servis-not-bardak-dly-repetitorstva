import sqlite3
from flask import current_app

def get_db():
    conn = sqlite3.connect(current_app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def init_db(app):
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        
        cursor.executescript('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password TEXT,
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
                user_id INTEGER NOT NULL,
                username TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                info TEXT DEFAULT 'привет, я использую веб сервис для репетиторства!',
                class_is INTEGER DEFAULT 0,
                photo TEXT DEFAULT 'nkvtf.jpg'
            );
            
            CREATE TABLE IF NOT EXISTS achievements (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                info TEXT NOT NULL,
            );
            
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY,
                sender TEXT DEFAULT 'tutor',
                viewer TEXT DEFAULT 'tutor',
                text TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        
        cursor.execute('''
            INSERT OR IGNORE INTO users (username, password, is_admin)
            VALUES (?, ?, 1)
        ''', ('Титова И.В.', 'Ilusha12!'))
        cursor.execute('''
            INSERT OR IGNORE INTO users (username, password, is_admin)
            VALUES (?, ?, 1)
        ''', ('zavric228', '12345679'))
        
        cursor.execute('INSERT OR IGNORE INTO profile (user_id) VALUES (1)')
        db.commit()