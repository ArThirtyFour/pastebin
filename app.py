from flask import Flask , render_template , redirect , session , request
import datetime
import sqlite3
import os
import hashlib


app = Flask(__name__)
bd=sqlite3.connect('users.db',check_same_thread=False)
cursor=bd.cursor()
app.config['SECRET_KEY'] = os.urandom(20).hex()
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(days=365)

@app.route('/')
def main():
    if 'user_name' not in session :
        return redirect('/login')
    else:
        pasta=cursor.execute('SELECT * FROM pasta').fetchall()
        return render_template('base.html',nick_name=session['user_name'],pastes=pasta)


@app.route('/login',methods=['GET','POST'])
def log():
    if request.method == 'GET':
        if 'error' not in session:
            return render_template('login.html',error=0)
        else:
            return render_template('login.html',error=session['error'])
    elif request.method == 'POST':
        session.permanent = True
        log , password = request.form['login'].lower() , hashlib.md5(request.form['password'].encode()).hexdigest()
        a = cursor.execute('SELECT * FROM users WHERE login = ?',(log,)).fetchone()
        if a and a[1] == password:
            session['error'],session['user_name'] = 0 , request.form['login']
            return redirect ('/')
        elif a and a[1] != password:
            session['error'] = 2
            return redirect('/login')
        elif a == None:
            session['error'] = 1
            return redirect('/login')


@app.route('/register',methods=['GET','POST'])
def res():
    if request.method == 'GET':
        print(session)
        if 'error' not in session:
            return render_template('register.html',error=0)
        else:
            return render_template('register.html',error=session['error'])
    elif request.method == 'POST':
        session.permanent = True
        if len(request.form['login'].lower())>=5 and len(request.form['password'])>=8:
            session['error'], = 0 , 
            login , password = request.form['login'] , hashlib.md5(request.form['password'].encode()).hexdigest()
            try:
                cursor.execute('INSERT INTO users VALUES (?,?)',(login,password))
                bd.commit()
                session['user_name'] = request.form['login']
                return redirect('/')
            except sqlite3.IntegrityError:
                session['error'] = 2
                return redirect('/register')
        else:
            session['error'] = 1
            return redirect('/register')
        
@app.route('/logout',methods=['GET','POST'])
def logout():
    session.permanent = True
    if 'user_name' in session:
        session.pop('user_name', None)
        return redirect ('/login')
    else:
        session['error'] = 1
        return redirect ('/login')


@app.route('/add_paste',methods=['GET','POST'])
def add_db():
    print(session)
    if request.method == 'GET':
        if 'user_name' not in session :
            return redirect('/login')
        else:
            return render_template('add_paste.html',nick_name=session['user_name'])
    if request.method == 'POST':
        try:
            nick ,url, title , text = session['user_name'],'/paste/'+request.form['title'],request.form['title'],request.form['paste']
            formatted_datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute('INSERT INTO pasta VALUES (?,?,?,?,?)',(nick,url,title,text,formatted_datetime))
            bd.commit()
            return redirect(f'/paste/{request.form["title"]}')
        except sqlite3.IntegrityError:
            return redirect('/')
@app.route('/paste/<name>')
def paste(name):
    if 'user_name' not in session:
        return redirect('/')
    else:
        pasta = cursor.execute('SELECT * FROM pasta WHERE title = ?',(name,)).fetchone()
        if pasta:
            paste = pasta[3].split('\r')
            author , title , time = pasta[0] , pasta[2] , pasta[4]
            return render_template('paste.html',text=paste,title=title,author=author,time=time)
            
        elif pasta == None:
            return render_template('404.html')
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html')       


if __name__ == '__main__':
    app.run(debug=True)