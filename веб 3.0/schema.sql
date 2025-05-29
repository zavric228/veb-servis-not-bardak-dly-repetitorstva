BEGIN TRANSACTION;

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

COMMIT; 