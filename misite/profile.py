# Добавить в начало файла
import os
from flask import Blueprint, session, request, redirect, url_for, flash, render_template, abort, jsonify, current_app
from werkzeug.utils import secure_filename


profile_bp = Blueprint('profile', __name__)

@profile_bp.route('/')
def index():
    if "rol" not in session:
        session["rol"]=0

    db = get_db()
    profile = db.execute('SELECT * FROM profile WHERE user_id = 1').fetchone()
    acs = db.execute('SELECT * FROM achievements WHERE').fetchall()
    ach,stuach = [i for i in acs if i[user_id]==1], [i for i in acs if i[user_id]!=1]

    return render_template('index.html', title='Репетитор',
        profile=dict(profile) if profile else {},
        achievements=ach,
        student_achievements=stuach,
        rol=session.get('rol', 0),
        logged_in='user' in session
    )

@profile_bp.route('/student_profile')
def student_profile():
    if 'rol' not in session or sessoin['rol']:
        return redirect('/')
    db = get_db()
    student = db.execute('SELECT * FROM students WHERE user_id = ?', (session['user_id'],)).fetchone()
    achivs = db.execute('SELECT * FROM achievements WHERE user_id = ?', (session['user_id'],)).fetchone()

    messages = db.execute('''
        SELECT * FROM messages 
        WHERE sender = ? OR viewer = ?
        ORDER BY timestamp DESC
    ''', (session['user'], session['user'])).fetchall()
    db.commit()

    return render_template('index.html', title=session['name'],
        profile=dict(profile) if profile else {},
        achievements=ach,
        student_achievements=stuach,
        rol=session.get('rol', 0),
        logged_in='user' in session
    )

@profile_bp.route('/update_profile', methods=['POST'])
def update_profile():
    if 'user' not in session or not session.get('is_admin', False):
        abort(403)
    
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
    return redirect(url_for('index'))

@profile_bp.route('/update_student_profile', methods=['POST'])
def update_student_profile():
    if 'user' not in session:
        abort(403)
    
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
    return redirect(url_for('profile.student_profile'))

@profile_bp.route('/api/students')
def api_students():
    if 'user' not in session or not session.get('is_admin', False):
        abort(403)
    
    query = request.args.get('q', '')
    db = get_db()
    students = db.execute('''
        SELECT id, username, name 
        FROM students 
        WHERE username LIKE ? 
        LIMIT 10
    ''', (f'%{query}%',)).fetchall()
    return jsonify([dict(row) for row in students])

@profile_bp.route('/admin_panel')
def admin_panel():
    if not session.get('is_admin', False):
        abort(403)
    
    db = get_db()
    messages = db.execute('''
        SELECT m.*, s.photo as student_photo 
        FROM messages m
        LEFT JOIN students s ON m.sender = s.username
        ORDER BY m.timestamp DESC
    ''').fetchall()
    
    return render_template('admin_panel.html', messages=messages)