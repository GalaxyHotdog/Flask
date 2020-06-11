from datetime import datetime
from Blog import db, login_manager
from flask_login import UserMixin
from sqlalchemy.ext.hybrid import hybrid_property

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_path = db.Column(
        db.String(120), nullable=False, default="default.jpg")
    password = db.Column(db.String(80), nullable=False)
    posts = db.relationship('Post', backref='author', lazy=True)
    comments = db.relationship('Comment', backref='author', lazy=True)
    liked = db.relationship('PostLike',foreign_keys='PostLike.user_id',backref='user', lazy='dynamic')
    uploader = db.relationship('FileContents', backref='author', lazy=True)
    followed = db.relationship('Following', foreign_keys="Following.user_id", backref='user', lazy='dynamic')
    follows = db.relationship('Following', foreign_keys="Following.following_id", backref='follows', lazy='dynamic')
    def like_post(self, post):
        if not self.has_liked_post(post):
            like = PostLike(user_id=self.id, post_id=post.id)
            db.session.add(like)

    def unlike_post(self, post):
        if self.has_liked_post(post):
            PostLike.query.filter_by(
                user_id=self.id,
                post_id=post.id).delete()

    def has_liked_post(self, post):
        return PostLike.query.filter(
            PostLike.user_id == self.id,
            PostLike.post_id == post.id).count() > 0

    def follow_user(self, user):
        if not self.has_followed_user(user):
            follow = Following(user_id=self.id, following_id=user.id)
            db.session.add(follow)

    def unfollow_user(self, user):
        if self.has_followed_user(user):
            Following.query.filter_by(
                user_id=self.id,
                following_id=user.id).delete()

    def has_followed_user(self, user):
        return Following.query.filter(
            Following.user_id == self.id,
            Following.following_id == user.id).count() > 0

    def __repr__(self):
        return f"User('{self.email}','{self.username}')"

class PostLike(db.Model):
    __tablename__ = 'post_like'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))

class Following(db.Model):
    __tablename__ = 'following'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    following_id = db.Column(db.Integer, db.ForeignKey('user.id'))


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False,
                            default=datetime.utcnow)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(20), nullable=False)
    image_path = db.Column(
        db.String(120), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    comments = db.relationship('Comment', backref='ref_post', lazy=True)
    likes = db.relationship('PostLike', backref='post', lazy='dynamic')

    def __repr__(self):
        return f"Post('{self.title}', '{self.date_posted}')"

    def num_likes(self):
        return self.likes.count()

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date_posted = db.Column(db.DateTime, nullable=False,
                            default=datetime.utcnow)
    content = db.Column(db.Text, nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Comment('{self.id}', '{self.date_posted}', '{self.post_id})"

class FileContents(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(300))
    data = db.Column(db.LargeBinary)
    date_uploaded = db.Column(db.DateTime, nullable=False,
                            default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"FileContents('{self.name}','{self.user_id}')"
