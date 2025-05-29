from flask import Blueprint, session, request, redirect, url_for, flash, render_template
import os

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form.get('password', '')
        
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        
        if user['user_id'] < 3:
            if user['password'] != password:
                flash('Неверный пароль администратора', 'error')
                return redirect(url_for('auth.login'))
            
            session['user'] = user['username']
            session['rol'] = 2
            return redirect(url_for('index'))
        else:
            if not user:
                # Создаем нового пользователя
                db.execute('INSERT INTO users (username) VALUES (?)', (username,))
                db.commit()
                
                db.execute('INSERT INTO students (username,name) VALUES (?)', (username, username))
                db.commit()

                user['name'] = username
                
                # Создаем начальное сообщение для чата
                db.execute('''
                    INSERT INTO messages (viewer, text) 
                    VALUES (?, ?)
                ''', (username, 'Чат создан'))
                db.commit()
            
            session['user'] = username
            session['rol'] = 1
            session['name'] = user['name']
            session['user_id'] = user['user_id']
            return redirect(url_for('student_profile'))
    
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))