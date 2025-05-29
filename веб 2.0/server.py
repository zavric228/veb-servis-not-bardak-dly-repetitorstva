from flask import Flask, render_template, session, redirect, abort, request, flash
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.secret_key = '228228228228'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://zavric228:Ilusha12@localhost/tutor_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'

db = SQLAlchemy(app)

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)
    print('adm')

class Child(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    achievements = db.relationship('Achievement', backref='child', lazy=True)
    print('Chi')

class Achievement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    child_id = db.Column(db.Integer, db.ForeignKey('child.id'), nullable=False)
    subject = db.Column(db.String(20), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(200), nullable=False)
    print('ach')

class Education(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(200), nullable=False)
    print('Edu')

class home_work(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    child_id = db.Column(db.String(100), nullable=False)
    date_end = db.Column(db.DateTime, nullable=False)
    print('how')

with app.app_context():
    db.create_all()
    admins = {'Евгения Владимировна': 'password'}
    for username, password in admins.items():
        existing_admin = Admin.query.filter_by(username=username).first()
        if not existing_admin:
            admin = Admin(username=username, password=password)
            db.session.add(admin)
    db.session.commit()

@app.route('/')
def first_page():
    return render_template('first_page.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login_post():
    log = request.form.get('log')
    if not log:
        flash('Поле не должно быть пустым', 'warning')
        return redirect('/login')
    admin = Admin.query.filter_by(username=log).first()
    if admin:
        session['secret_id'] = True
        return redirect(f'/secret/{log}')
    session['secret_id'] = False
    session['name'] = log
    return redirect('/')

@app.route('/secret/<string:log>')
def secret(log):
    if 'secret_id' not in session or not session['secret_id']:
        return redirect('/')
    return render_template('secret_page.html', log=log)

@app.route('/secret_key/<string:log>', methods=['POST'])
def secret_key(log):
    pasw = request.form.get('pasw')
    if pasw == 'Ilusha12!':
        session['name'] = log
        return redirect('/admin')
    flash('Пароль неверный', 'warning')
    return render_template('secret_page.html', log=log)

@app.route('/admin')
def admin():
    if 'secret_id' not in session or not session['secret_id']:
        return redirect('/')
    return render_template('admin_page.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/dark')
def dark_theme():
    session['theme'] = 'dark'
    return redirect(request.referrer or '/')

@app.route('/light')
def light_theme():
    session['theme'] = 'light'
    return redirect(request.referrer or '/')

@app.route('/profil')
def profil():
    if 'theme' not in session:
        session['theme'] = 'light'
    return render_template('profil.html', theme=session['theme'])

if __name__ == '__main__':
    app.run(debug=True, port=8080)