from flask import Flask, render_template, redirect, session, request, flash
from database import engine, users, pastes
import datetime
import os
import secrets
import hashlib
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf.csrf import CSRFProtect

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(20))
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(days=365)
app.config['WTF_CSRF_ENABLED'] = True
csrf = CSRFProtect(app)

@app.route('/')
def main():
    if 'user_name' not in session:
        return redirect('/login')
    with engine.connect() as conn:
        pasta = conn.execute(pastes.select().order_by(pastes.c.date.desc())).fetchall()
        return render_template('base.html', nick_name=session['user_name'], pastes=pasta)

@app.route('/login', methods=['GET', 'POST'])
def log():
    if request.method == 'GET':
        return render_template('login.html', error=session.get('error', 0))
    
    session.permanent = True
    login = request.form.get('login', '').lower().strip()
    password = request.form.get('password', '')
    
    if not login or not password:
        session['error'] = 3
        return redirect('/login')
    
    with engine.connect() as conn:
        user = conn.execute(
            users.select().where(users.c.login == login)
        ).fetchone()
        
        if user:
            md5_password = hashlib.md5(password.encode()).hexdigest()
            
            if check_password_hash(user[1], password) or user[1] == md5_password:
                if user[1] == md5_password:
                    try:
                        conn.execute(
                            users.update().
                            where(users.c.login == login).
                            values(password=generate_password_hash(password))
                        )
                        conn.commit()
                    except Exception as e:
                        app.logger.error(f"Ошибка при обновлении хеша пароля: {str(e)}")
                
                session['error'] = 0
                session['user_name'] = login
                return redirect('/')
        
        session['error'] = 2 if user else 1
        return redirect('/login')

@app.route('/register', methods=['GET', 'POST'])
def res():
    if request.method == 'GET':
        return render_template('register.html', error=session.get('error', 0))
    
    session.permanent = True
    login = request.form.get('login', '').lower().strip()
    password = request.form.get('password', '')
    
    if not login or not password:
        session['error'] = 3
        return redirect('/register')
    
    if len(login) >= 5 and len(password) >= 8:
        try:
            with engine.connect() as conn:
                existing_user = conn.execute(
                    users.select().where(users.c.login == login)
                ).fetchone()
                
                if existing_user:
                    session['error'] = 2
                    return redirect('/register')
                
                hashed_password = generate_password_hash(password)
                
                conn.execute(
                    users.insert().values(
                        login=login,
                        password=hashed_password
                    )
                )
                conn.commit()
            session['user_name'] = login
            session['error'] = 0
            return redirect('/')
        except Exception as e:
            app.logger.error(f"Ошибка при регистрации: {str(e)}")
            session['error'] = 2
            return redirect('/register')
    else:
        session['error'] = 1
        return redirect('/register')

@app.route('/logout', methods=['GET'])
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
    
    title = request.form.get('title', '').strip()
    paste_content = request.form.get('paste', '').strip()
    
    if not title or not paste_content:
        flash('Заголовок и содержимое обязательны')
        return redirect('/add_paste')
    
    slug = title.lower().replace(' ', '-')
    
    try:
        with engine.connect() as conn:
            existing_paste = conn.execute(
                pastes.select().where(pastes.c.title == title)
            ).fetchone()
            
            if existing_paste:
                flash('Паста с таким заголовком уже существует')
                return redirect('/add_paste')
            
            conn.execute(
                pastes.insert().values(
                    user=session['user_name'],
                    url='/paste/' + slug,
                    title=title,
                    paste=paste_content,
                    date=datetime.datetime.now()
                )
            )
            conn.commit()
        return redirect(f'/paste/{slug}')
    except Exception as e:
        app.logger.error(f"Ошибка при добавлении пасты: {str(e)}")
        flash('Ошибка при сохранении пасты')
        return redirect('/add_paste')

@app.route('/paste/<slug>')
def paste(slug):
    if 'user_name' not in session:
        return redirect('/')
    try:
        with engine.connect() as conn:
            pasta = conn.execute(
                pastes.select().where(pastes.c.url == f'/paste/{slug}')
            ).fetchone()
            
            if not pasta:
                pasta = conn.execute(
                    pastes.select().where(pastes.c.title == slug)
                ).fetchone()
            
            if pasta:
                paste = pasta[3].split('\r')
                author, title, time = pasta[0], pasta[2], pasta[4]
                return render_template('paste.html', text=paste, title=title, author=author, time=time)
            return render_template('404.html')
    except Exception as e:
        app.logger.error(f"Ошибка при просмотре пасты: {str(e)}")
        return render_template('404.html')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html')

if __name__ == '__main__':
    app.run(debug=True)