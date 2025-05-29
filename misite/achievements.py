from flask import Blueprint, session, request, redirect, url_for, flash, current_app
import os
from werkzeug.utils import secure_filename


achievements_bp = Blueprint('achievements', __name__)

@achievements_bp.route('/add_achievement', methods=['POST'])
def add_achievement():
    if 'user' not in session or not session.get('is_admin', False):
        abort(403)
    info = request.form['info']  # Получаем описание всегда
    student_username = request.form.get('student_username').strip()

    if student_username.lower() == 'репетитор':
        user_id = 1
    else:
        student = db.execute('SELECT id FROM students WHERE username = ?', (student_username,)).fetchone()
        user_id = student['user_id']
        db.commit()
    db = get_db()
    db.execute('INSERT INTO achievements (user_if, info) VALUES (?, ?)', (user_id, info))
    db.commit()
    flash('Достижение добавлено', 'success')
    return redirect(url_for('index'))

@achievements_bp.route('/delete_achievement/<int:id>')
def delete_achievement(id):
    if 'user' not in session or session['rol']:
        abort(403)
    db = get_db()
    achievement = db.execute('SELECT * FROM achievements WHERE id = ?', (id,)).fetchone()
    
    if not achievement:
        flash('Достижение не найдено', 'error')
        db.commit()
        return redirect(url_for('index'))
    
    db.execute('DELETE FROM achievements WHERE id = ?', (id,))
    db.commit()
    flash('Достижение удалено', 'success')
    return redirect(url_for('index'))