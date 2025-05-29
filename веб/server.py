from flask import Flask, render_template, session, redirect, abort, request
from flask_sqlalchemy import SQLAlchemy

# Инициализация Flask-приложения
app = Flask(__name__)
app.secret_key = '228228228228'  # Секретный ключ для сессий

# Настройка подключения к PostgreSQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://zavric228:Ilusha12@localhost/tutor_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Инициализация SQLAlchemy
db = SQLAlchemy(app)

# Модель для администраторов
class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)

# Модель для детей
class Child(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    achievements = db.relationship('Achievement', backref='child', lazy=True)

# Модель для достижений
class Achievement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    child_id = db.Column(db.Integer, db.ForeignKey('child.id'), nullable=False)
    subject = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(200), nullable=False)

# Создание таблиц в базе данных и добавление начальных данных
with app.app_context():
    db.create_all()

    # Добавление начальных данных (если нужно)
    admins = {'Евгения Владимировна': 'Ilusha12'}
    for username, password in admins.items():
        # Проверяем, существует ли пользователь
        existing_admin = Admin.query.filter_by(username=username).first()
        if not existing_admin:  # Если пользователь не существует
            admin = Admin(username=username, password=password)
            db.session.add(admin)
    db.session.commit()

# Маршрут для главной страницы
@app.route('/')
def index():
    if 'theme' not in session:
        session['theme'] = 'math'  # По умолчанию выбрана математика
    if 'name' not in session:
        session['name'] = '[имя не определено]'
    if 'theem' not in session:
        session['theem'] = 'light'
    return render_template('index.html', theme=session['theme'], name=session['name'], theem=session['theem'])

# Маршрут для страницы входа
@app.route('/login')
def login():
    return render_template('login.html')

# Обработка POST-запроса для входа
@app.route('/login', methods=['post'])
def login_post():
    log = request.form.get('log')
    if len(log):
        admin = Admin.query.filter_by(username=log).first()
        if admin:
            session['secret_id'] = True
            return redirect('/secret/' + log)
        session['secret_id'] = False
        session['name'] = log
        return redirect('/')
    return render_template('login.html', mis=1)

# Маршрут для страницы группы
@app.route('/gr/<string:group>')
def gr(group):
    if group not in ['math', 'music', 'plants']:
        return render_template('404.html'), 404
    session['theme'] = group
    return redirect('/')

# Маршрут для страницы блока
@app.route('/gr/<string:group>/bl/<string:block>')
def bl(group, block):
    if group not in ['math', 'music', 'plants']:
        return render_template('404.html'), 404
    themes = ['theme1', 'theme2', 'theme3']  # Замените на реальные темы
    if block not in themes:
        return render_template('404.html'), 404
    return render_template('block.html', group=group, block=block)

# Маршрут для выхода
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# Маршрут для темной темы
@app.route('/dark')
def dark_theem():
    session['theem'] = 'dark'
    return redirect('/')

# Маршрут для светлой темы
@app.route('/light')
def light_theem():
    session['theem'] = 'light'
    return redirect('/')

# Маршрут для секретной страницы
@app.route('/secret/<string:log>')
def secret(log):
    if 'secret_id' not in session or not session['secret_id']:
        return redirect('/')
    return render_template('secret_page.html', log=log)

# Обработка POST-запроса для секретной страницы
@app.route('/secret_key/<string:log>', methods=['post'])
def secret_key(log):
    pasw = request.form.get('pasw')
    if pasw == 'Ilusha12!':
        session['name'] = log
        return redirect('/')
    return render_template('secret_page.html', mis=1, log=log)

# Запуск сервера
if __name__ == '__main__':
    app.run(debug=True, port=8080)