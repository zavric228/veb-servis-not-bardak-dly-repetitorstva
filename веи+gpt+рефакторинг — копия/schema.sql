BEGIN TRANSACTION;

-- Таблица пользователей
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password TEXT,
    is_admin BOOLEAN DEFAULT 0
);

-- Профиль преподавателя
CREATE TABLE IF NOT EXISTS profile (
    user_id INTEGER PRIMARY KEY,
    name TEXT DEFAULT '',
    phone TEXT DEFAULT '',
    email TEXT DEFAULT '',
    telegram TEXT DEFAULT '',
    photo TEXT DEFAULT 'nkvtf.jpg'
);

-- Ученики
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    photo TEXT DEFAULT 'nkvtf.jpg',
    name TEXT DEFAULT '',
);

-- Достижения
CREATE TABLE IF NOT EXISTS achievements (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    image TEXT NOT NULL,
    description TEXT NOT NULL,
    is_student BOOLEAN DEFAULT 0,
    student_id INTEGER
);

-- Сообщения чата
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY,
    sender TEXT NOT NULL,
    text TEXT NOT NULL,
    file TEXT,
    student_id INTEGER REFERENCES students(id),
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Данные администратора (логин: zavric228, пароль: 12345679)
INSERT OR IGNORE INTO users (username, password, is_admin) 
VALUES (
    'zavric228', 
    'pbkdf2:sha256:260000$XcD9aJ9H$8e4f1d3e7f0a2b5c6d8e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1', 
    1
);

-- Пустой профиль преподавателя
INSERT OR IGNORE INTO profile (user_id) VALUES (1);

COMMIT;