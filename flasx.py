from flask import Flask, render_template, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_mail import Mail
from werkzeug.utils import secure_filename
import json
import math
import os

with open('config.json', 'r') as c:
    parameter = json.load(c)["parameter"]

local_server = True

app = Flask(__name__)

app.secret_key = 'super-secret-key'

app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT='465',
    MAIL_USE_SSL=True,
    MAIL_USERNAME=parameter['gmail-user'],            # give your own gmail id to get message in json file
    MAIL_PASSWORD=parameter['gmail-password']         # give your gmail pw in json file
)
mail = Mail(app)

if local_server:
    app.config['SQLALCHEMY_DATABASE_URI'] = parameter['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = parameter['prod_uri']

db = SQLAlchemy(app)


class Contact(db.Model):
    serial = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(25), nullable=False)
    message = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=True)


class Posts(db.Model):
    serial = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=True)
    slug = db.Column(db.String(80), nullable=True)
    subtitle = db.Column(db.String(500), nullable=True)
    content = db.Column(db.String(5000), nullable=True)
    img_file = db.Column(db.String(12), nullable=True)
    date = db.Column(db.String(12), nullable=True)


class Gallery(db.Model):
    serial = db.Column(db.Integer, primary_key=True)
    img = db.Column(db.String(25), unique=True, nullable=True)
    date = db.Column(db.String(12), nullable=True)


class Subs(db.Model):
    serial = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(12), nullable=True)
    date = db.Column(db.String(12), nullable=True)


@app.route("/")
def page1():
    posts = Posts.query.filter_by().all()
    last = math.ceil(len(posts) / int(parameter['no_of_posts']))
    page = request.args.get('page')
    if not str(page).isnumeric():
        page = 1
    page = int(page)
    posts = posts[
     (page - 1) * int(parameter['no_of_posts']):(page - 1) * int(parameter['no_of_posts'])+int(parameter['no_of_posts'])
            ]
    if page == 1:
        prev = "#"
        nex = "/?page=" + str(page + 1)
    elif page == last:
        prev = "/?page=" + str(page - 1)
        nex = "#"
    else:
        prev = "/?page=" + str(page - 1)
        nex = "/?page=" + str(page + 1)
    return render_template('Home.html', parameter=parameter, posts=posts, prev=prev, nex=nex)


@app.route("/post/<string:post_slug>", methods=['GET'])
def post_route(post_slug):
    post = Posts.query.filter_by(slug=post_slug).first()
    return render_template('post.html', parameter=parameter, post=post)


@app.route("/about")
def page2():
    return render_template('About.html', parameter=parameter)


@app.route("/login", methods=['GET', 'POST'])
def page3():

    if 'user' in session and session['user'] == parameter['admin-email']:
        posts = Posts.query.all()
        gallery_data = Gallery.query.all()
        return render_template('dashboard.html', parameter=parameter, posts=posts, gallery=gallery_data)

    if request.method == 'POST':
        uname = request.form.get('username')
        upass = request.form.get('pass')
        if uname == parameter['admin-email'] and upass == parameter['admin_password']:
            session['user'] = uname
            posts = Posts.query.all()
            gallery_data = Gallery.query.all()
            return render_template('dashboard.html', parameter=parameter, posts=posts, gallery=gallery_data)

    return render_template('Login.html', parameter=parameter)


@app.route("/subs", methods=['GET', 'POST'])
def page4():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        date = request.form.get('date')

        arrival = Subs(name=name, email=email, date=datetime.now())
        db.session.add(arrival)
        db.session.commit()

        mail.send_message(
            'New Message from ' + name,
            sender=email,
            recipients=[parameter['gmail-user']],
            body=name + ' has just subscribed to your Newsletter'
        )
    return render_template('Subscribe.html', parameter=parameter)


@app.route("/gallery")
def page5():
    gallery_data = Gallery.query.all()
    return render_template('Gallery.html', parameter=parameter, gallery=gallery_data)


@app.route("/contact", methods=['GET', 'POST'])
def page6():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')
        date = request.form.get('date')

        entry = Contact(name=name, email=email, message=message,  date=datetime.now())
        db.session.add(entry)
        db.session.commit()

        mail.send_message('New Message from ' + name,
                          sender=email,
                          recipients=[parameter['gmail-user']],
                          body=message)
    return render_template('Contact.html', parameter=parameter)


title = 'title'
subtitle = 'subtitle'
slug = 'slug'
content = 'content'
img_file = 'img_file'
img = 'img'
date = datetime.now()


@app.route('/uploader', methods=('GET', 'POST'))
def uploader():
    if 'user' in session and session['user'] == parameter['admin-email']:
        if request.method == 'POST':
            f = request.files['file1']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
            return "Uploaded Successfully"


@app.route('/create', methods=('GET', 'POST'))
def create():
    global title, slug, content, img_file, date, subtitle
    if 'user' in session and session['user'] == parameter['admin-email']:
        if request.method == 'POST':
            title = request.form.get(title)
            subtitle = request.form.get(subtitle)
            slug = request.form.get(slug)
            content = request.form.get(content)
            img_file = request.form.get(img_file)
            date = datetime.now()

            post = Posts(title=title, slug=slug, content=content, subtitle=subtitle, img_file=img_file, date=date)
            db.session.add(post)
            db.session.commit()

    post = Posts.query.filter_by().first()
    return render_template('create.html', parameter=parameter, post=post)


@app.route('/image', methods=('GET', 'POST'))
def image():
    global img, date
    if 'user' in session and session['user'] == parameter['admin-email']:
        if request.method == 'POST':
            img = request.form.get('img')
            date = datetime.now()

            post_image = Gallery(img=img, date=date)
            db.session.add(post_image)
            db.session.commit()

    post_image = Gallery.query.filter_by().first()
    return render_template('image.html', parameter=parameter, post_image=post_image)


@app.route('/logout')
def logout():
    session.pop('user')
    return redirect('/login')


@app.route("/delete/<string:serial>", methods=('GET', 'POST'))
def delete(serial):
    if 'user' in session and session['user'] == parameter['admin-email']:
        post = Posts.query.filter_by(serial=serial).first()
        db.session.delete(post)
        db.session.commit()
    return redirect('/login')


@app.route("/del/<string:serial>", methods=('GET', 'POST'))
def clear(serial):
    if 'user' in session and session['user'] == parameter['admin-email']:
        gallery_data = Gallery.query.filter_by(serial=serial).first()
        db.session.delete(gallery_data)
        db.session.commit()
    return redirect('/login')


@app.route("/edit/<string:serial>", methods=('GET', 'POST'))
def edit(serial):
    post = Posts.query.filter_by(serial=serial).first()
    global title, slug, content, img_file, date, subtitle
    if 'user' in session and session['user'] == parameter['admin-email']:
        if request.method == 'POST':
            post.title = request.form.get(title)
            post.subtitle = request.form.get(subtitle)
            post.slug = request.form.get(slug)
            post.content = request.form.get(content)
            post.img_file = request.form.get(img_file)
            post.date = datetime.now()
            db.session.commit()
            return redirect('/edit/' + serial)
    post = Posts.query.filter_by(serial=serial).first()
    return render_template('Edit.html', parameter=parameter, post=post)


@app.route("/change/<string:serial>", methods=('GET', 'POST'))
def change(serial):
    gallery_data = Gallery.query.filter_by(serial=serial).first()
    global img_file, date
    if 'user' in session and session['user'] == parameter['admin-email']:
        if request.method == 'POST':
            gallery_data.img = request.form.get(img)
            gallery_data.date = datetime.now()
            db.session.commit()
            return redirect('/change/' + serial)
    gallery_data = Gallery.query.filter_by(serial=serial).first()
    return render_template('change.html', parameter=parameter, gallery=gallery_data)


if __name__ == "__main__":
    app.run(host='localhost', debug=True)
