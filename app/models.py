from app import db, login, app
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from sqlalchemy.sql import column
from time import time
import jwt


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    goog_id = db.Column(db.String, unique=True, index=True)
    firstname = db.Column(db.String, index=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index = True, unique = True)
    password_hash = db.Column(db.String(128))
    articles = db.relationship('Article', backref='user', lazy='dynamic')
    highlights = db.relationship('Highlight', backref ='user', lazy ='dynamic')
    topics = db.relationship('Topic', backref = 'user', lazy = 'dynamic')
    tags = db.relationship('Tag', backref = 'user', lazy = 'dynamic')

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password':self.id, 'exp':time() + expires_in},
            app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])['reset_password']
        except:
            return
        return User.query.get(id)

@login.user_loader
def load_user(id):
    return User.query.get(int(id))

class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    unread = db.Column(db.Boolean, index=True)
    title = db.Column(db.String(255), index=True)
    source = db.Column(db.String(500))
    content = db.Column(db.String)
    date_read = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    highlights = db.relationship('Highlight', backref = 'article', lazy='dynamic')

highlights_topics = db.Table('highlights_topics',
    db.Column('highlight_id', db.Integer, db.ForeignKey('highlight.id'), nullable=False),
    db.Column('topic_id', db.Integer, db.ForeignKey('topic.id'), nullable=False )
)

class Highlight(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    text = db.Column(db.String, index=True) #should I set a max length?
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    article_id = db.Column(db.Integer, db.ForeignKey('article.id'))
    topics = db.relationship('Topic', secondary=highlights_topics, backref = 'highlight', lazy='dynamic')
    note = db.Column(db.String, index=True) 

    # add highlight to topic
    def AddToTopic(self, topic):
        if not self.is_added(topic):
            self.topics.append(topic)
       
    # remove highlight from topic
    def RemoveFromTopic(self, topic):  
        if self.is_added(topic):
            self.topics.remove(topic)
      
    # checks if a highlight is in a topic
    def is_added(self, topic):
        return self.topics.filter(
            topic.id == highlights_topics.c.topic_id).count() > 0
    
    # returns all topics that a highlight is a part of.  highlight.in_topics.all()
    def in_topics(self):
        return Topic.query.join(
            highlights_topics, (highlights_topics.c.topic_id == Topic.id)
            ).filter(
               highlights_topics.c.highlight_id == self.id
               ) 
   
    # returns all topics that a highlight is not a part of. highlight.not_in_topics()
    def not_in_topics(self):
        query = Topic.query.filter(
            Topic.id.notin_(
                db.session.query(highlights_topics.c.topic_id).filter(
                    highlights_topics.c.highlight_id == self.id)))
        list = []
        for i in query:
            list.append(i)

        return list
    
    
    

class Topic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(512), unique=True, index=True) #how long should it be?
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    highlights = db.relationship('Highlight', secondary=highlights_topics, backref = 'topic', lazy='dynamic')
    archived = db.Column(db.Boolean, index=True)

    def is_added(self, highlight):
        return self.highlights.filter(
            highlight.id == highlights_topics.c.highlight_id).count() > 0

class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    archived = db.Column(db.Boolean, index=True)
    goal = db.Column(db.String(512))

