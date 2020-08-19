from app import db, login
from datetime import datetime
from flask import current_app, url_for
from flask_login import UserMixin, current_user
import jwt
from sqlalchemy.sql import column
from time import time
from werkzeug.security import generate_password_hash, check_password_hash


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
    account_created_date = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password':self.id, 'exp':time() + expires_in},
            current_app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])['reset_password']
        except:
            return
        return User.query.get(id)

    # api return user resource
    def to_dict(self):
        tags = self.tags.all()
        tag_names = []
        for tag in tags:
            tag_names.append(tag.name)
        
        data = {
            'id': self.id,
            'tags': tag_names,    
            '_links': {
                'self': url_for('api.get_user_tags', id=self.id),
                'articles': url_for('api.add_article', id=self.id)
            }
        }
        return data

@login.user_loader
def load_user(id):
    return User.query.get(int(id))


tags_articles = db.Table('tags_articles',
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), nullable=False),
    db.Column('article_id', db.Integer, db.ForeignKey('article.id'), nullable=False )
)


class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    unread = db.Column(db.Boolean, index=True)
    title = db.Column(db.String(255), index=True)
    filetype = db.Column(db.String(32)) 
    source = db.Column(db.String(500))
    source_url = db.Column(db.String(500))
    content = db.Column(db.Text)
    date_read = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    highlights = db.relationship('Highlight', backref = 'article', lazy='dynamic')
    archived = db.Column(db.Boolean, index=True)
    highlightedText = db.Column(db.String)
    tags = db.relationship('Tag', secondary=tags_articles, backref = 'article', lazy='dynamic')

    #api return article resource
    def to_dict(self):
        data = {
            'article_id':self.id,
            '_links': {
                'self': url_for('api.add_article', id=self.id),
                'tags': url_for('api.get_user_tags', id=self.id),
            }
        }
        return data



    # add article to tag
    def AddToTag(self, tag):
        if not self.is_added(tag):
            self.tags.append(tag)
       
    # remove article from tag
    def RemoveFromTag(self, tag):  
        if self.is_added(tag):
            self.topics.remove(tag)
      
    # checks if an article is in a tag
    def is_added(self, tag):
        return self.tags.filter(
            tag.id == tags_articles.c.tag_id).count() > 0
    
    #returns true if article is untagged
    def not_added(self):
        """
        Highlight.query.join(
            highlights_topics, (highlights_topics.c.highlight_id == Highlight.id
            ).filter(
                Highlight.archived==False, Highlight.user_id==current_user.id,
                Highlight.id.notin_(
                    db.session.query(highlights_topics))).all()
        """
        query = db.session.query(tags_articles).filter(tags_articles.c.article_id == self.id).count()

        if query == 0:
            return True
        else:
            return False
    

    
    # returns all tagss that an article is a part of.  article.in_tags().all()
    def in_tags(self):
        return Tag.query.join(
            tags_articles, (tags_articles.c.tag_id == Tag.id)
            ).filter(
               tags_articles.c.article_id == self.id, Tag.archived==False, Tag.user_id==current_user.id
               ) 
   
    # returns all tags that an article is not a part of. article.not_in_tags().all()
    def not_in_tags(self):
        return Tag.query.filter(
            Tag.archived==False, Tag.user_id==current_user.id,
            Tag.id.notin_(
                db.session.query(tags_articles.c.tag_id).filter(
                    tags_articles.c.article_id == self.id))).all()
        




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
    archived = db.Column(db.Boolean, index=True)


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
    
  
    def not_added(self):
        """
        Highlight.query.join(
            highlights_topics, (highlights_topics.c.highlight_id == Highlight.id
            ).filter(
                Highlight.archived==False, Highlight.user_id==current_user.id,
                Highlight.id.notin_(
                    db.session.query(highlights_topics))).all()
        """
        query = db.session.query(highlights_topics).filter(highlights_topics.c.highlight_id == self.id).count()

        if query == 0:
            return True
        else:
            return False
    

    
    # returns all topics that a highlight is a part of.  highlight.in_topics().all()
    def in_topics(self):
        return Topic.query.join(
            highlights_topics, (highlights_topics.c.topic_id == Topic.id)
            ).filter(
               highlights_topics.c.highlight_id == self.id, Topic.archived==False, Topic.user_id==current_user.id

               ) 
   
    # returns all topics that a highlight is not a part of. highlight.not_in_topics()
    def not_in_topics(self):
        query = Topic.query.filter(
            Topic.archived==False, Topic.user_id==current_user.id,
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
    articles = db.relationship('Article', secondary=tags_articles, backref = 'tag', lazy='dynamic')

