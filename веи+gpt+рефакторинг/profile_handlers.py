from flask import Blueprint, render_template, request, session, redirect, url_for, flash, abort, jsonify, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import sqlite3
import os
import logging
from datetime import datetime

profile_bp = Blueprint('profile', __name__)
logger = logging.getLogger(__name__)

def get_db():
    conn = sqlite3.connect(current_app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

@profile_bp.route('/')
def index():
    try:
        db = get_db()
        profile = db.execute('SELECT * FROM profile WHERE user_id = 1').fetchone()
        achievements = db.execute('''
            SELECT * FROM achievements 
            WHERE is_student = 0  -- Только репетитор
        ''').fetchall()

        student_achievements = db.execute('''
            SELECT a.*, s.username 
            FROM achievements a
            JOIN students s ON a.student_id = s.id 
            WHERE is_student = 1  -- Только ученики
        ''').fetchall()
    
        return render_template('index.html',
                            profile=dict(profile) if profile else {},
                            achievements=achievements,
                            student_achievements=student_achievements,
                            is_admin=session.get('is_admin', False),
                            logged_in='user' in session)
    except Exception as e:
        logger.error(f"Ошибка загрузки главной страницы: {str(e)}")
        abort(500)

@profile_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form.get('password', '')  # Пароль только для админа
        
        try:
            db = get_db()
            user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
            
            # Авторизация администратора
            if username.lower() == 'zavric228':
                if not user or not check_password_hash(user['password'], password):
                    flash('Неверный пароль администратора', 'error')
                    return redirect(url_for('profile.login'))
                
                session['user'] = user['username']
                session['is_admin'] = True
                return redirect(url_for('profile.index'))
            
            # Автоматическая регистрация/вход ученика
            else:
                if not user:
                    # Создаем запись ученика
                    db.execute('INSERT INTO users (username) VALUES (?)', (username,))
                    db.execute('INSERT INTO students (username) VALUES (?)', (username,))
                    db.commit()
                
                session['user'] = username
                session['is_admin'] = False
                return redirect(url_for('profile.index'))
        
        except Exception as e:
            logger.error(f"Ошибка авторизации: {str(e)}")
            flash('Ошибка сервера', 'error')
    
    return render_template('login.html')

@profile_bp.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    if len(username) > 100:
        flash('Логин слишком длинный (максимум 100 символов)', 'error')
        return redirect(url_for('login'))
    
    try:
        db = get_db()
        db.execute('INSERT INTO users (username) VALUES (?)', (username,))
        db.execute('INSERT INTO students (username) VALUES (?)', (username,))
        db.commit()
        session['user'] = username
        session['is_admin'] = False
        return redirect(url_for('index'))
    except sqlite3.IntegrityError:
        flash('Этот логин уже занят', 'error')
        return redirect(url_for('login'))
    except Exception as e:
        logger.error(f"Ошибка регистрации: {str(e)}")
        flash('Ошибка регистрации', 'error')
        return redirect(url_for('login'))

@profile_bp.route('/student_profile')
def student_profile():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    try:
        db = get_db()
        student = db.execute('SELECT * FROM students WHERE username = ?', (session['user'],)).fetchone()
        
        if not student:
            student = {'username': session['user'], 'photo': 'nkvtf.jpg', 'name': ''}
            db.execute('INSERT INTO students (username) VALUES (?)', (student['username'],))
            db.commit()
        
        messages = db.execute('''
            SELECT * FROM messages 
            WHERE sender = ? OR sender = 'tutor'
            ORDER BY timestamp DESC
        ''', (session['user'],)).fetchall()
    
        return render_template('sections/student_profile.html',
                            student=dict(student),
                            messages=messages)
    except Exception as e:
        logger.error(f"Ошибка профиля ученика: {str(e)}")
        abort(500)

@profile_bp.route('/update_profile', methods=['POST'])
def update_profile():
    if 'user' not in session or not session.get('is_admin', False):
        abort(403)
    
    try:
        name = request.form['name']
        phone = request.form['phone']
        email = request.form['email']
        telegram = request.form['telegram']
        
        db = get_db()
        db.execute('''
            INSERT OR REPLACE INTO profile 
            (user_id, name, phone, email, telegram) 
            VALUES (1, ?, ?, ?, ?)
        ''', (name, phone, email, telegram))
        
        if 'photo' in request.files:
            file = request.files['photo']
            if file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                upload_folder = current_app.config['UPLOAD_FOLDER_PROFILE']
                file.save(os.path.join(upload_folder, filename))
                db.execute('UPDATE profile SET photo = ? WHERE user_id = 1', (filename,))
        
        db.commit()
        flash('Профиль успешно обновлён', 'success')
    except Exception as e:
        logger.error(f"Ошибка обновления профиля: {str(e)}")
        flash('Ошибка обновления профиля', 'error')
    
    return redirect(url_for('index'))

@profile_bp.route('/add_achievement', methods=['POST'])
def add_achievement():
    if 'user' not in session or not session.get('is_admin', False):
        abort(403)
    
    try:
        # Проверка обязательного файла
        if 'image' not in request.files or request.files['image'].filename == '':
            flash('Файл изображения обязателен', 'error')
            return redirect(url_for('profile.index'))
        
        file = request.files['image']
        if not allowed_file(file.filename):
            flash('Недопустимый формат файла', 'error')
            return redirect(url_for('profile.index'))
        
        # Получение данных формы
        description = request.form['description']
        student_username = request.form.get('student_username', '').strip()
        is_student = 1
        student_id = None

        # Определение типа достижения
        if student_username.lower() == 'репетитор':
            is_student = 0
        else:
            db = get_db()
            student = db.execute(
                'SELECT id FROM students WHERE username = ?', 
                (student_username,)
            ).fetchone()
            
            if not student:
                db.execute('INSERT INTO students (username) VALUES (?)', (student_username,))
                db.commit()
                student = db.execute(
                    'SELECT id FROM students WHERE username = ?', 
                    (student_username,)
                ).fetchone()
            
            student_id = student['id']

        # Сохранение файла
        filename = secure_filename(file.filename)
        upload_folder = (
            current_app.config['UPLOAD_FOLDER_STUDENTS_ACHIEVEMENTS'] 
            if is_student 
            else current_app.config['UPLOAD_FOLDER_ACHIEVEMENTS']
        )
        file.save(os.path.join(upload_folder, filename))

        # Сохранение в БД
        db = get_db()
        db.execute('''
            INSERT INTO achievements 
            (user_id, image, description, is_student, student_id) 
            VALUES (1, ?, ?, ?, ?)
        ''', (filename, description, is_student, student_id))
        db.commit()
        flash('Достижение добавлено', 'success')
    
    except Exception as e:
        logger.error(f"Ошибка добавления достижения: {str(e)}")
        flash('Ошибка добавления достижения', 'error')
    
    return redirect(url_for('profile.index'))

@profile_bp.route('/delete_achievement/<int:id>', methods=['POST'])
def delete_achievement(id):
    if 'user' not in session or not session.get('is_admin', False):
        abort(403)
    
    try:
        db = get_db()
        achievement = db.execute('SELECT * FROM achievements WHERE id = ?', (id,)).fetchone()
        
        if not achievement:
            flash('Достижение не найдено', 'error')
            return redirect(url_for('index'))
        
        upload_folder = (
            current_app.config['UPLOAD_FOLDER_STUDENTS_ACHIEVEMENTS'] 
            if achievement['is_student'] 
            else current_app.config['UPLOAD_FOLDER_ACHIEVEMENTS']
        )
        file_path = os.path.join(upload_folder, achievement['image'])
        
        if os.path.exists(file_path) and achievement['image'] != 'default_achievement.jpg':
            os.remove(file_path)
        
        db.execute('DELETE FROM achievements WHERE id = ?', (id,))
        db.commit()
        flash('Достижение удалено', 'success')
    except Exception as e:
        logger.error(f"Ошибка удаления достижения: {str(e)}")
        flash('Ошибка удаления достижения', 'error')
    
    return redirect(url_for('index'))

@profile_bp.route('/update_student_profile', methods=['POST'])
def update_student_profile():
    if 'user' not in session:
        abort(403)
    
    try:
        student_id = request.form['student_id']
        name = request.form['name']
        class_is = request.form['class_is'] 
        
        db = get_db()
        if not session['is_admin']:
            student = db.execute('SELECT username FROM students WHERE id = ?', (student_id,)).fetchone()
            if not student or student['username'] != session['user']:
                abort(403)
        
        update_data = {'name': name, 'class_is': class_is}
        if 'photo' in request.files:
            file = request.files['photo']
            if file.filename and allowed_file(file.filename):
                filename = secure_filename(f"{student_id}_{file.filename}")
                upload_folder = current_app.config['UPLOAD_FOLDER_STUDENTS_ACHIEVEMENTS']
                file.save(os.path.join(upload_folder, filename))
                update_data['photo'] = filename
        
        db.execute('''
            UPDATE students 
            SET name = :name, 
                class_is = :class_is, 
                photo = COALESCE(:photo, photo) 
            WHERE id = :id
        ''', {**update_data, 'id': student_id})
        db.commit()
        flash('Профиль ученика обновлён', 'success')
    except Exception as e:
        logger.error(f"Ошибка обновления профиля ученика: {str(e)}")
        flash('Ошибка обновления профиля ученика', 'error')
    
    return redirect(url_for('profile.student_profile'))

@profile_bp.route('/api/students')
def api_students():
    if 'user' not in session or not session.get('is_admin', False):
        abort(403)
    
    try:
        query = request.args.get('q', '')
        db = get_db()
        students = db.execute('''
            SELECT id, username, name 
            FROM students 
            WHERE username LIKE ? 
            LIMIT 10
        ''', (f'%{query}%',)).fetchall()
        return jsonify([dict(row) for row in students])
    except Exception as e:
        logger.error(f"Ошибка API поиска учеников: {str(e)}")
        abort(500)