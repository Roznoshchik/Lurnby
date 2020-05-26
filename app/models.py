from app import db, login
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    goog_id = db.Column(db.String, unique=True, index=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index = True, unique = True)
    password_hash = db.Column(db.String(128))
    articles = db.relationship('Article', backref='user', lazy='dynamic')
    highlights = db.relationship('Highlight', backref ='user', lazy ='dynamic')
    topics = db.relationship('Topic', backref = 'user', lazy = 'dynamic')

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    

@login.user_loader
def load_user(id):
    return User.query.get(int(id))

class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    unread = db.Column(db.Boolean, index=True)
    title = db.Column(db.String(255), index=True)
    url = db.Column(db.String(500))
    content = db.Column(db.String)
    date_read = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    highlights = db.relationship('Highlight', backref = 'article', lazy='dynamic')

highlights_topics = db.Table('highlights_topics',
    db.Column('highlight_id', db.Integer, db.ForeignKey('highlight.id'), primary_key=True),
    db.Column('topic_id', db.Integer, db.ForeignKey('topic.id'), primary_key=True)
)

class Highlight(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    text = db.Column(db.String, index=True) #should I set a max length?
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    article_id = db.Column(db.Integer, db.ForeignKey('article.id'))
    topics = db.relationship('Topic', secondary=highlights_topics, backref = 'highlight', lazy='dynamic')


class Topic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(512), index=True) #how long should it be?
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    highlights = db.relationship('Highlight', secondary=highlights_topics, backref = 'topic', lazy='dynamic')
    archived = db.Column(db.Boolean, index=True)



