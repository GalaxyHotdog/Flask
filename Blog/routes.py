from flask import render_template, url_for, redirect, flash, request, abort, send_file
from Blog.models import User, Post, Comment, FileContents, PostLike, Following
from Blog.forms import RegisterForm, LoginForm, UpdateAccountForm, PostForm, CommentForm, SearchForm, ChangePasswordForm
from Blog import app, db, bcrypt
from flask_login import login_user, logout_user, current_user, login_required
import secrets
import os
from PIL import Image
from sqlalchemy import desc
from io import BytesIO
from datetime import datetime, timedelta

@app.route("/")
@app.route("/home")
def home():
    current_time = datetime.utcnow()
    ten_weeks_ago = current_time - timedelta(days=7)
    posts = Post.query.outerjoin(PostLike).group_by(Post.id).filter(Post.date_posted > ten_weeks_ago).order_by(db.func.count(PostLike.id).desc(), Post.date_posted.desc()).limit(5).all()
    posts_all = Post.query.order_by(Post.date_posted.desc()).all()
    return render_template('home.html', posts=posts, posts_all=posts_all)

@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegisterForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(
            form.password.data).decode('utf-8')
        user = User(username=form.username.data,
                    email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash(f'Account created!', 'success')
        login_user(user, remember=False)
        return redirect(url_for('home'))
    return render_template('register.html', title='Register', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('/'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            else:
                return redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check your email and password', 'danger')
    return render_template('login.html', title='Login', form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))

def save_file(form_picture):
    random_hash = secrets.token_hex(12)
    _, f_ex = os.path.split(form_picture.filename)
    picture_file = random_hash + f_ex
    picture_path = os.path.join(
        app.root_path, 'static/profile_pics', picture_file)
    form_picture.save(picture_path)
    return form_picture

def save_picture(form_picture):
    random_hash = secrets.token_hex(12)
    _, f_ex = os.path.split(form_picture.filename)
    picture_file = random_hash + f_ex
    picture_path = os.path.join(
        app.root_path, 'static/profile_pics', picture_file)
    target_size = (300, 300)
    new_picture = Image.open(form_picture)
    new_picture.thumbnail(target_size)

    new_picture.save(picture_path)
    return picture_file


def save_picture_post(form_picture):
    random_hash = secrets.token_hex(12)
    _, f_ex = os.path.split(form_picture.filename)
    picture_file = random_hash + f_ex
    picture_path = os.path.join(
        app.root_path, 'static/post_pics', picture_file)
    target_size = (650, 451)
    new_picture = Image.open(form_picture)
    new_picture.thumbnail(target_size)

    new_picture.save(picture_path)
    return picture_file


@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    posts = Post.query.filter_by(author=current_user).order_by(
        Post.date_posted.desc()).all()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_path = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for(
        'static', filename='profile_pics/' + current_user.image_path)
    return render_template('account.html', title='Account',
                           image_file=image_file, form=form, posts=posts)


@app.route("/changepassword", methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if  bcrypt.check_password_hash(current_user.password, form.old_password.data):
            hashed_new_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
            current_user.password = hashed_new_password
            db.session.commit()
            flash('Password changed!', 'success')
            return redirect(url_for('account'))
        else:
            flash('Error. Please check your email and password', 'danger')
    return render_template('change_password.html',title='Change Password', form=form)
            




@app.route("/post/new", methods=['GET', 'POST'])
@login_required
def create_post():
    form = PostForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture_post(form.picture.data)
        else:
            picture_file = None
        post = Post(title=form.title.data, content=form.content.data,
                    category=form.category.data, image_path=picture_file, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your post has been created!', 'success')
        return redirect(url_for('home'))
    return render_template('create_post.html', title='New Post',
                           form=form)
#form = PostForm()
#        if form.validate_on_submit():
#         if form.picture.data:
#             picture_file = save_picture(form.picture.data)
#         else:
#             picture_file = None
#         post = Post(title=form.title.data, content=form.content.data, category=form.category.data , image_path=picture_file ,author=current_user)
#         db.session.add(post)
#         db.session.commit()
#         flash('Your new post has been created and been posted.', 'success')
#         return redirect(url_for('home'))
#     return render_template('create_post.html', title="Create New Post", form=form, legend='Create New Post')


@app.route("/post/<int:post_id>", methods=['GET', 'POST'])
def post(post_id):
    post = Post.query.get(post_id)
    comments = Comment.query.filter_by(post_id=post_id).order_by(
        Comment.date_posted.desc()).all()
    if post:
        return render_template('post.html', title=post.title, post=post, comments=comments)


@app.route("/post/<int:post_id>/update", methods=['GET', 'POST'])
@login_required
def update_post(post_id):
    post = Post.query.get(post_id)
    if post.author != current_user:
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        post.category = form.category.data
        if form.picture.data is None:
            db.session.commit()
            flash('Your post has been updated', 'success')
            return redirect(url_for('post', post_id=post_id))
        else:
            picture_file = save_picture_post(form.picture.data)
            post.image_path = picture_file
            db.session.commit()
            flash('Your post has been updated', 'success')
            return redirect(url_for('post', post_id=post_id))
    elif request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content
        form.category.data = post.category
    return render_template('create_post.html', title="Update Post", form=form, legend='Update Post')


@app.route("/post/<int:post_id>/delete", methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get(post_id)
    if post.author != current_user:
        abort(403)
    Comment.query.filter_by(post_id=post.id).delete()
    db.session.delete(post)
    db.session.commit()
    return redirect(url_for('home'))


@app.route("/post/<int:post_id>/comment", methods=['GET', 'POST'])
@login_required
def create_comment(post_id):
    post = Post.query.get(post_id)
    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(content=form.content.data,
                          author=current_user, ref_post=post)
        db.session.add(comment)
        db.session.commit()
        return redirect(url_for('post', post_id=post.id))
    return render_template('create_comment.html', title=post.title, post=post, legend='New Comment', form=form)


@app.route('/like/<int:post_id>/<action>')
@login_required
def like_action(post_id, action):
    post = Post.query.filter_by(id=post_id).first_or_404()
    if action == 'like':
        current_user.like_post(post)
        db.session.commit()
    if action == 'unlike':
        current_user.unlike_post(post)
        db.session.commit()
    return redirect(request.referrer)


@app.route("/catagory/<string:category>")
def post_categoried(category):
    posts = Post.query.filter_by(category=category).order_by(
        Post.date_posted.desc()).all()
    return render_template('home.html', posts=posts, category=category)


@app.route("/search", methods=['GET', 'POST'])
def search():
    form = SearchForm()
    if form.validate_on_submit():
        if form.method.data == 'key':
            key = '%' + form.key.data + '%'
        else:
            key = form.key.data
        posts = Post.query.filter(
            (Post.title.like(key) ) | (Post.content.like(key))).all()
        return render_template('home.html', posts=posts)
    return render_template('search.html', form=form)

@app.route("/upload", methods=['POST'])
@login_required
def upload():
    newfile = request.files['inputFile']
    new_file = FileContents(name=newfile.filename, data=newfile.read(), author=current_user)
    db.session.add(new_file)
    db.session.commit()
    flash(f'File uploaded!', 'success')
    return redirect(url_for('resources'))

@app.route("/download/<int:file_id>", methods=['GET', 'POST'])
@login_required
def download(file_id):
    File = FileContents.query.get(file_id)
    return send_file(BytesIO(File.data),attachment_filename=File.name, as_attachment=True)


@app.route("/resources", methods=['POST', 'GET'])
@login_required
def resources():
    files = FileContents.query.order_by(FileContents.date_uploaded.desc()).all()
    return render_template('resources.html', files=files, title='Resources')
    
@app.route('/follow/<int:user_id>/<action>')
@login_required
def follow_action(user_id, action):
    user = User.query.filter_by(id=user_id).first_or_404()
    if action == 'follow':
        current_user.follow_user(user)
        db.session.commit()
    if action == 'unfollow':
        current_user.unfollow_user(user)
        db.session.commit()
    return redirect(request.referrer)

@app.route('/myfollowing')
@login_required
def list_following():
    #Post.query.outerjoin(PostLike).group_by(Post.id).filter(Post.date_posted > ten_weeks_ago).order_by(db.func.count(PostLike.id).desc(), Post.date_posted.desc()).limit(5).all()
    following = User.query.join(Following, User.id==Following.following_id).filter(Following.user_id==current_user.id).all()
    return render_template('following.html', follows=following)


@app.route('/post-<int:user_id>')
def user_post(user_id):
    user = User.query.get(user_id)
    posts = Post.query.filter_by(author=user).order_by(Post.date_posted.desc()).all()
    return render_template('userpost.html',posts=posts)
