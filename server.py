from flask import Flask, render_template, session, redirect, abort, request

app = Flask(__name__)
app.secret_key = '228228228'

secret_id=0

admins={}
names=open('spice/admins.txt')
for i in names:
    admins[i.strip()]='Ilusha12'
names.close()
admins['Евгения Владимировна']='Ilusha12'
print(admins)


@app.route('/')
def index():
    if 'secret_id' not in session:
        session['secret_id']=0
    print('s_i =',session['secret_id'])
    if 'name' not in session or session['name']=='[Имя не определено]':
        session['had_name']=False
    else:
        session['had_name']=True
    print('h_n =',session['had_name'])
    if 'name' not in session:
        session['name']='[имя не определено]'
    print('пользователь',session['name'],'теперь на /')
    if 'theem' not in session:
        session['theem']='light'
        return render_template('first_page.html')
    
    return render_template('index.html', mis=0, name=session['name'], tit='Главная страница', theem=session['theem'])

@app.route('/login')
def login():
    if 'theem' not in session:
        return redirect('/')
    if 'had_name' not in session:
        return redirect('/')
    print('пользователь',session['name'],'теперь на /login')
    if session['had_name']:
        return render_template('login.html', mis=0, tit='вход')
    return redirect('/')

@app.route('/login', methods=['post'])
def login_post():
    log = request.form.get('log')
    print('пользователь',session['name'],'придумал себе имя', log, 'размером в', len(log))
    if len(log):
        print(admins)
        if log in admins:
            session['secret_id']=True
            return redirect('/secret/'+log)
        session['secret_id']=False
        session['name']=log
        session['had_name']=True
        return redirect('/')
    print('пользователь',session['name'],"- идиот, он указал имя: ''")
    return render_template('login.html', mis=1, tit='вход')

#===========================================================================================================================

@app.route('/gr/<string:group>')
def gr(group):
    if 'secret_id' not in session:
        session['secret_id']=False
    if 'theem' not in session:
        return redirect('/')
    if group not in ['math','music','plants']:
        print('пользователь',session['name'],'- идиот, он перешёл на /group/'+group)
        return render_template('index.html', mis=3, tit='главная страница', theem=session['theem'], n=session['had_name'])
    thems=open('spice/'+group+'/thems.txt')
    themes=[i.strip() for i in thems]
    thems.close()
    print('пользователь',session['name'],'теперь на /group/'+group)
    return render_template('grupp.html', mis=0, tit=group, theem=session['theem'], themes=themes)

@app.route('/gr/<string:group>/bl/<string:block>')
def bl(group,block):
    if 'secret_id' not in session:
        session['secret_id']=False
    if 'theem' not in session:
        return redirect('/')
    thems=open('spice/'+group+'/thems.txt')
    themes=[i.strip() for i in thems]
    thems.close()
    if group not in ['math','music','plants'] or block not in themes:
        print('пользователь',session['name'],'- идиот, он перешёл на /group/'+group+'/bl/'+block)
        return render_template('index.html', mis=3, tit='главная страница', theem=session['theem'], n=session['had_name'])
    images=open('spice/'+group+'/'+block+'/images')
    img=[i.strip() for i in images]
    images.close()
    HomeWork=open('spice/'+group+'/'+block+'/HW')
    hw=[i.strip() for i in HomeWork]
    HomeWork.close
    print('пользователь',session['name'],'теперь на /gr/'+group+'/bl/'+block)
    return render_template('block.html', img=img, hw=hw, name=session['name'])

@app.route('/logout')
def logout():
    print('пользователь',session['name'],'стал ананимусом')
    if 'name' in session:
        session['name']='[имя не определено]'
    if 'had_name' in session:
        session['had_name']=False
    #del session['theem']
    return redirect('/')

@app.route('/dark')
def dark_theem():
    session['theem']='dark'
    print('пользователь',session['name'],'изменил тему на ['+session['theem']+']')
    return redirect('/')

@app.route('/light')
def light_theem():
    session['theem']='light'
    print('пользователь',session['name'],'изменил тему на ['+session['theem']+']')
    return redirect('/')

@app.route('/secret/<string:log>')
def secret(log):
    if 'secret_id' not in session:
        redirect('/')
    if not session['secret_id']:
        print('пользователь',session['name'],'перешёл на секретную страницу не являясь админом')
        return redirect('/')
    return render_template('secret_page.html',log=log)

@app.route('/secret_key/<string:log>', methods=['post'])
def secret_key(log):
    pasw=request.form.get('pasw')
    if 'Ilusha12!'==pasw:
        print('пользователь',session['name'],'оказался админом:',log)
        session['name']=log
        return redirect('/')
    print('пользователь',session['name'],'пытается войти за админа:',log+', и вводит неверный пароль:',)
    return render_template('secret_page.html', mis=1, log=log)

app.run(debug=True, port=8080)