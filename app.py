import flask_login
import manager
from flask import Flask, render_template, current_app, request, redirect, flash, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, login_required
from flask_login import LoginManager
import pyshorteners
from hashids import Hashids
import urllib.request
from datetime import datetime


app = Flask(__name__)
app.secret_key = "super secret key"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///base.db'
db = SQLAlchemy(app)
manager = LoginManager(app)

hashids = Hashids(min_length=5, salt=app.config['SECRET_KEY'])

with app.app_context():
    # within this block, current_app points to app.
    print(current_app.name)

class User(UserMixin,db.Model):
    id = db.Column(db.Integer, primary_key =True) #Уникальный ключ
    Login = db.Column(db.String(50), nullable=False, unique = True)
    Password = db.Column(db.String(50), nullable=False)
    short_url = db.relationship('Short_url', backref='user', lazy='dynamic')

    def __repr__(self):
        return '<Login %r>' % self.id

class Short_url(db.Model):
    id = db.Column(db.Integer, primary_key =True) #Уникальный ключ
    id_user = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # логин id
    URL = db.Column(db.String(300), nullable=False)
    Short_URL = db.Column(db.String(300), nullable=False)
    Date = db.Column(db.DateTime, default=datetime.utcnow)
    Clicks = db.Column(db.Integer, nullable=False, default = 0)

    def __repr__(self):
        return '<Article %r>' % self.id

@manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

@app.route('/', methods=['GET', 'POST'])
def login_page():
    login = request.form.get('login')
    password = request.form.get('password')

    if login and password:
        user = User.query.filter_by(Login=login).first()

        if user and user.Password == password:
            login_user(user)

            return redirect("/link")
        else:
            flash('Login or password is not correct')
    else:
        flash('Please fill login and password fields')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    login = request.form.get('login')
    password = request.form.get('password')
    password2 = request.form.get('password2')

    if request.method == 'POST':
        if not (login or password or password2):
            flash('Please, fill all fields!')
        elif password != password2:
            flash('Passwords are not equal!')
        else:
            new_user = User(Login=login, Password=password)
            db.session.add(new_user)
            db.session.commit()

            return redirect(url_for('login_page'))

    return render_template('register.html')


def is_valid(url): # проверка на адекватность ссылки
    try:
        urllib.request.urlopen(url)
        return True
    except Exception:
        return False


@app.route('/link', methods=['GET', 'POST'])
@login_required
def links():
    data = Short_url.query.filter_by(id_user=flask_login.current_user.id).all()
    if request.method == "POST":
        url = request.form.get('url')


        if is_valid(url):
            s = pyshorteners.Shortener().tinyurl.short(url) # создание короткой ссылки
            Short = Short_url(id_user=flask_login.current_user.id, URL=url, Short_URL = s)
            db.session.add(Short)  # добавляем объект
            db.session.commit()


            flash(s)
        else:
            flash("Link is not correct!")
    return render_template("links.html", data = data)


@app.route('/<int:id>', methods=['GET'])
@login_required
def url_redirect(id):
    data = Short_url.query.filter_by(id=id).first()
    if data.id_user == flask_login.current_user.id:
        url = data.Short_URL
        data.Clicks = data.Clicks + 1
        db.session.commit()
        return redirect(url)
    else:
        return redirect(url_for('links'))



if __name__ == '__main__':
    app.run(debug = True, port=5000, host='127.0.0.1')


