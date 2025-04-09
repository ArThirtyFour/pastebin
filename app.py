from flask import Flask, render_template, redirect, session, request
from database import engine, users, pastes
import datetime
import os
import hashlib

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(20).hex()
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(days=365)

@app.route('/')
def main():
    if 'user_name' not in session:
        return redirect('/login')
    with engine.connect() as conn:
        pasta = conn.execute(pastes.select()).fetchall()
        return render_template('base.html', nick_name=session['user_name'], pastes=pasta)

@app.route('/login', methods=['GET', 'POST'])
def log():
    if request.method == 'GET':
        return render_template('login.html', error=session.get('error', 0))
    
    session.permanent = True
    login = request.form['login'].lower()
    password = hashlib.md5(request.form['password'].encode()).hexdigest()
    
    with engine.connect() as conn:
        user = conn.execute(
            users.select().where(users.c.login == login)
        ).fetchone()
        
        if user and user[1] == password:
            session['error'] = 0
            session['user_name'] = request.form['login']
            return redirect('/')
        session['error'] = 2 if user else 1
        return redirect('/login')

@app.route('/register', methods=['GET', 'POST'])
def res():
    if request.method == 'GET':
        return render_template('register.html', error=session.get('error', 0))
    
    session.permanent = True
    login = request.form['login'].lower()
    password = hashlib.md5(request.form['password'].encode()).hexdigest()
    
    if len(login) >= 5 and len(request.form['password']) >= 8:
        try:
            with engine.connect() as conn:
                conn.execute(
                    users.insert().values(
                        login=login,
                        password=password
                    )
                )
                conn.commit()
            session['user_name'] = request.form['login']
            session['error'] = 0
            return redirect('/')
        except:
            session['error'] = 2
            return redirect('/register')
    else:
        session['error'] = 1
        return redirect('/register')

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.permanent = True
    if 'user_name' in session:
        session.pop('user_name', None)
        return redirect('/login')
    else:
        session['error'] = 1
        return redirect('/login')

@app.route('/add_paste', methods=['GET', 'POST'])
def add_db():
    if 'user_name' not in session:
        return redirect('/login')
        
    if request.method == 'GET':
        return render_template('add_paste.html', nick_name=session['user_name'])
        
    try:
        with engine.connect() as conn:
            conn.execute(
                pastes.insert().values(
                    user=session['user_name'],
                    url='/paste/' + request.form['title'],
                    title=request.form['title'],
                    paste=request.form['paste'],
                    date=datetime.datetime.now()
                )
            )
            conn.commit()
        return redirect(f'/paste/{request.form["title"]}')
    except:
        return redirect('/')

@app.route('/paste/<name>')
def paste(name):
    if 'user_name' not in session:
        return redirect('/')
    with engine.connect() as conn:
        pasta = conn.execute(
            pastes.select().where(pastes.c.title == name)
        ).fetchone()
        if pasta:
            paste = pasta[3].split('\r')
            author, title, time = pasta[0], pasta[2], pasta[4]
            return render_template('paste.html', text=paste, title=title, author=author, time=time)
        return render_template('404.html')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html')

if __name__ == '__main__':
    app.run(debug=True)