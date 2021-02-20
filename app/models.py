import base64
from app import db, login
from datetime import datetime, timedelta
from flask import current_app, url_for
from flask_login import UserMixin
import jwt
import uuid
import os
from sqlalchemy import desc
from sqlalchemy_utils import UUIDType
from time import time
from werkzeug.security import generate_password_hash, check_password_hash


preferences = '{"font": "sans-serif","color": "light-mode", \
              "size": "4","spacing": "line-height-min"}'


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    goog_id = db.Column(db.String, unique=True, index=True)
    firstname = db.Column(db.String, index=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    articles = db.relationship('Article', backref='user', lazy='dynamic')
    highlights = db.relationship('Highlight', backref='user', lazy='dynamic')
    topics = db.relationship('Topic', backref='user', lazy='dynamic')
    tags = db.relationship('Tag', backref='user', lazy='dynamic')
    account_created_date = db.Column(db.DateTime, default=datetime.utcnow)
    token = db.Column(db.String(32), index=True, unique=True)
    token_expiration = db.Column(db.DateTime)
    preferences = db.Column(db.String, index=True, default=preferences)
    admin = db.Column(db.Boolean)
    test_account = db.Column(db.Boolean)

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            current_app.config['SECRET_KEY'],
            algorithm='HS256').decode('utf-8')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, current_app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except jwt.exceptions.InvalidTokenError:
            return
        return User.query.get(id)

    # api return user resource
    def to_dict(self):
        tags = self.tags.filter_by(archived=False).all()
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

    def from_dict(self, data):
        for field in ['username', 'email']:
            setattr(self, field, data[field])
        self.set_password(data['password'])

    def get_token(self, expires_in=2592000):
        now = datetime.utcnow()
        if self.token and self.token_expiration > now + timedelta(seconds=60):
            return self.token
        self.token = base64.b64encode(os.urandom(24)).decode('utf-8')
        self.token_expiration = now + timedelta(seconds=expires_in)
        db.session.add(self)
        return self.token

    def revoke_token(self):
        self.token_expiration = datetime.utcnow() - timedelta(seconds=1)

    @staticmethod
    def check_token(token):
        user = User.query.filter_by(token=token).first()
        if user is None or user.token_expiration < datetime.utcnow():
            return None
        return user


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


tags_articles = db.Table('tags_articles',
                         db.Column('tag_id', db.Integer,
                                   db.ForeignKey('tag.id'), nullable=False
                                   ), db.Column('article_id', db.Integer,
                                                db.ForeignKey('article.id'),
                                                nullable=False))


class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(UUIDType(), default=uuid.uuid4, index=True)
    unread = db.Column(db.Boolean, index=True, default=True)
    title = db.Column(db.String(255), index=True)
    filetype = db.Column(db.String(32))
    source = db.Column(db.String(500))
    source_url = db.Column(db.String(500))
    content = db.Column(db.Text)
    date_read = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    highlights = db.relationship('Highlight', lazy='dynamic')
    archived = db.Column(db.Boolean, index=True)
    highlightedText = db.Column(db.String, default='')
    tags = db.relationship('Tag', secondary=tags_articles, lazy='dynamic')
    progress = db.Column(db.Float, index=True, default=0.0)
    done = db.Column(db.Boolean, default=False)
    notes = db.Column(db.Text)
    article_created_date = db.Column(db.DateTime, default=datetime.utcnow)

    def recent_articles():
        return Article.query.filter_by(done=False,
                                       archived=False,
                                       unread=False
                                       ).order_by(desc(Article.date_read)
                                       ).limit(3).all()


    # api return article resource
    def to_dict(self):
        data = {
            'article_id': self.id,
            '_links': {
                'self': url_for('api.add_article', id=self.id),
                'tags': url_for('api.get_user_tags', id=self.id),
            }
        }
        return data

    # add article to tag
    def AddToTag(self, tag):
        if not self.is_added_tag(tag):
            self.tags.append(tag)
            for h in self.highlights:
                h.AddToTag(tag)

    # remove article from tag
    def RemoveFromTag(self, tag):
        if self.is_added_tag(tag):
            self.tags.remove(tag)
            for h in self.highlights:
                h.RemoveFromTag(tag)

    # checks if an article is in a tag
    def is_added_tag(self, tag):
        return self.tags.filter(
            tag.id == tags_articles.c.tag_id).count() > 0

    # returns true if article is untagged
    def not_added_tag(self):
        t_aid = tags_articles.c.article_id
        query = db.session.query(tags_articles
                                 ).filter(t_aid == self.id).count()

        if query == 0:
            return True
        else:
            return False

    # returns all tags that an article is not a part of.
    # article.not_in_tags().all()
    def not_in_tags(self, user):

        sub = db.session.query(Tag.id).outerjoin(
            tags_articles, tags_articles.c.tag_id == Tag.id).filter(
                tags_articles.c.article_id == self.id)

        q = db.session.query(Tag).filter(~Tag.id.in_(sub)
                                         ).filter_by(user_id=user.id).all()

        return q


highlights_topics = db.Table(
    'highlights_topics',
    db.Column('highlight_id', db.Integer, db.ForeignKey('highlight.id'),
              nullable=False, primary_key=True),
    db.Column('topic_id', db.Integer, db.ForeignKey('topic.id'),
              nullable=False, primary_key=True)
)


tags_highlights = db.Table(
    'tags_highlights',
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), nullable=False),
    db.Column('highlight_id', db.Integer, db.ForeignKey('highlight.id'),
              nullable=False)
)


class Highlight(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String, index=True)  # should I set a max length?
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    article_id = db.Column(db.Integer, db.ForeignKey('article.id'))
    topics = db.relationship(
        'Topic', secondary=highlights_topics, lazy='dynamic')
    note = db.Column(db.String, index=True)
    archived = db.Column(db.Boolean, index=True)
    tags = db.relationship('Tag', secondary=tags_highlights, lazy='dynamic')
    position = db.Column(db.String)

    # add highlight to topic
    def AddToTopic(self, topic):
        if not self.is_added_topic(topic):
            self.topics.append(topic)

    # remove highlight from topic
    def RemoveFromTopic(self, topic):
        if self.is_added_topic(topic):
            self.topics.remove(topic)

    # checks if a highlight is in a topic
    def is_added_topic(self, topic):
        return self.topics.filter(
            topic.id == highlights_topics.c.topic_id).count() > 0

    def not_added_topic(self):

        query = db.session.query(
            highlights_topics).filter(
                highlights_topics.c.highlight_id == self.id).count()

        if query == 0:
            return True
        else:
            return False

    def not_in_topics(self, user):
        sub = db.session.query(Topic.id).outerjoin(
            highlights_topics,
            highlights_topics.c.topic_id == Topic.id).filter(
                highlights_topics.c.highlight_id == self.id)
        q = db.session.query(
            Topic).filter(
                ~Topic.id.in_(sub)).filter_by(
                    user_id=user.id, archived=False).all()

        return q

    # add highlight to tag
    def AddToTag(self, tag):
        if not self.is_added_tag(tag):
            self.tags.append(tag)

    # remove highlight from tag
    def RemoveFromTag(self, tag):
        if self.is_added_tag(tag):
            self.tags.remove(tag)

    # checks if an highlight is in a tag
    def is_added_tag(self, tag):
        return self.tags.filter(
            tag.id == tags_highlights.c.tag_id).count() > 0

    # returns true if highlight is untagged
    def not_added_tag(self):

        query = db.session.query(
            tags_highlights).filter(
                tags_highlights.c.highlight_id == self.id).count()

        if query == 0:
            return True
        else:
            return False

    # returns all tags that a highlight is not a part of
    def not_in_tags(self, user):

        sub = db.session.query(Tag.id).outerjoin(
            tags_highlights, tags_highlights.c.tag_id == Tag.id).filter(
                tags_highlights.c.highlight_id == self.id)
        q = db.session.query(
            Tag).filter(~Tag.id.in_(sub)).filter_by(user_id=user.id).all()

        return q


tags_topics = db.Table(
    'tags_topics', db.Column('tag_id', db.Integer,
                             db.ForeignKey('tag.id'), nullable=False),
    db.Column('topic_id', db.Integer,
              db.ForeignKey('topic.id'), nullable=False)
)


class Topic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(512), index=True)  # how long should it be?
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    highlights = db.relationship(
        'Highlight', secondary=highlights_topics, lazy='dynamic')
    archived = db.Column(db.Boolean, index=True)
    tags = db.relationship('Tag', secondary=tags_topics, lazy='dynamic')

    # this checks if a specific highlight is in this topic
    def is_added_highlight(self, highlight):
        return self.highlights.filter(
            highlight.id == highlights_topics.c.highlight_id).count() > 0

    # add topic to tag
    def AddToTag(self, tag):
        if not self.is_added_tag(tag):
            self.tags.append(tag)

    # remove topic from tag
    def RemoveFromTag(self, tag):
        if self.is_added_tag(tag):
            self.tags.remove(tag)

    # checks if an topic is in a tag
    def is_added_tag(self, tag):
        return self.tags.filter(
            tag.id == tags_topics.c.tag_id).count() > 0

    # returns true if topic is untagged
    def not_added_tag(self):

        query = db.session.query(
            tags_topics).filter(tags_topics.c.topic_id == self.id).count()

        if query == 0:
            return True
        else:
            return False

    # returns all tags that a topic is not a part of
    def not_in_tags(self, user):

        sub = db.session.query(Tag.id).outerjoin(
            tags_topics, tags_topics.c.tag_id == Tag.id).filter(
                tags_topics.c.topic_id == self.id)
        q = db.session.query(
            Tag).filter(~Tag.id.in_(sub)).filter_by(user_id=user.id).all()

        return q


class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    archived = db.Column(db.Boolean, index=True, default=False)
    goal = db.Column(db.String(512))

    articles = db.relationship(
        'Article', secondary=tags_articles,  lazy='dynamic')

    highlights = db.relationship(
        'Highlight', secondary=tags_highlights,  lazy='dynamic')

    topics = db.relationship('Topic', secondary=tags_topics,  lazy='dynamic')

    # checks if a specific highlight is tagged
    def is_added_highlight(self, highlight):
        return self.highlights.filter(
            highlight.id == tags_highlights.c.highlight_id).count() > 0

    def is_added_topic(self, topic):
        return self.topics.filter(
            topic.id == tags_topics.c.topic_id).count() > 0

    def is_added_article(self, article):
        return self.articles.filter(
            article.id == tags_articles.c.article_id).count() > 0
