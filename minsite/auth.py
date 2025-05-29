from flask import Blueprint, session, request, redirect, url_for, flash, render_template
from database import get_db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form.get('password', '')
        
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        
        if username.lower() == 'zavric228':
            if not user or user['password'] != password:
                flash('Неверный пароль администратора', 'error')
                return redirect(url_for('auth.login'))
            
            session['user'] = user['username']
            session['is_admin'] = True
            return redirect(url_for('index'))
        else:
            if not user:
                db.execute('INSERT INTO users (username) VALUES (?)', (username,))
                db.execute('INSERT INTO students (username) VALUES (?)', (username,))
                db.commit()
            
            session['user'] = username
            session['is_admin'] = False
            return redirect(url_for('index'))
    
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))