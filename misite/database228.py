import sqlite3
from flask import current_app



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
                is_admin BOOLEAN DEFAULT 0
            );
            
            CREATE TABLE IF NOT EXISTS profile (
                user_id INTEGER PRIMARY KEY,
                name TEXT DEFAULT '',
                phone TEXT DEFAULT '',
                email TEXT DEFAULT '',
                telegram TEXT DEFAULT '',
                photo TEXT DEFAULT 'default.jpg'
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
                info TEXT NOT NULL,
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
        
        cursor.execute('''
            INSERT OR IGNORE INTO users (username, password, is_admin)
            VALUES (?, ?, 1)
        ''', ('zavric228', '12345679'))
        
        cursor.execute('INSERT OR IGNORE INTO profile (user_id) VALUES (1)')
        db.commit()