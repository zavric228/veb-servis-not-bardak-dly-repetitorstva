from flask import Blueprint, session, request, redirect, url_for, flash, current_app
from werkzeug.utils import secure_filename
from database import get_db, allowed_file

achievements_bp = Blueprint('achievements', __name__)

@achievements_bp.route('/add_achievement', methods=['POST'])
def add_achievement():
    if 'user' not in session or not session.get('is_admin', False):
        abort(403)
    
    if 'image' not in request.files or request.files['image'].filename == '':
        flash('Файл изображения обязателен', 'error')
        return redirect(url_for('index'))
    
    file = request.files['image']
    if not allowed_file(file.filename):
        flash('Недопустимый формат файла', 'error')
        return redirect(url_for('index'))
    
    info = request.form['info']
    student_username = request.form.get('student_username', '').strip()
    is_student = 1
    student_id = None

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

    filename = secure_filename(file.filename)
    upload_folder = (
        current_app.config['UPLOAD_FOLDER_STUDENTS_ACHIEVEMENTS'] 
        if is_student 
        else current_app.config['UPLOAD_FOLDER_ACHIEVEMENTS']
    )
    file.save(os.path.join(upload_folder, filename))

    db = get_db()
    db.execute('''
        INSERT INTO achievements 
        (user_id, image, info, is_student, student_id) 
        VALUES (1, ?, ?, ?, ?)
    ''', (filename, info, is_student, student_id))
    db.commit()
    flash('Достижение добавлено', 'success')
    return redirect(url_for('index'))

@achievements_bp.route('/delete_achievement/<int:id>', methods=['POST'])
def delete_achievement(id):
    if 'user' not in session or not session.get('is_admin', False):
        abort(403)
    
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
    return redirect(url_for('index'))