import base64
from app import db, login
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from flask import current_app, url_for
from flask_login import UserMixin, current_user
import jwt
import json
import uuid
import os
import random
import redis
import rq
from sqlalchemy import desc, func
from sqlalchemy_utils import UUIDType
import string
from time import time
from werkzeug.security import generate_password_hash, check_password_hash


preferences = '{"font": "sans-serif","color": "light-mode", \
              "size": "4","spacing": "line-height-min"}'

class Comms(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True)
    informational = db.Column(db.Boolean, default=True)
    educational = db.Column(db.Boolean, default=True)
    promotional = db.Column(db.Boolean, default=True)
    highlights = db.Column(db.Boolean, default=True)
    reminders = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<User {self.user_id}>\n informational: {self.informational}, educational: {self.educational}, promotional: {self.promotional}, highlights: {self.highlights}, reminders: {self.reminders}'

class User(UserMixin, db.Model):
    #########################
    ####    Identity    #####
    #########################
    id = db.Column(db.Integer, primary_key=True)
    goog_id = db.Column(db.String, unique=True, index=True)
    firstname = db.Column(db.String, index=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    admin = db.Column(db.Boolean)
    test_account = db.Column(db.Boolean, default=False)
    deleted = db.Column(db.Boolean, default=False)
    

    ##############################
    ####    Relationships    #####
    ##############################
    articles = db.relationship('Article', backref='user', lazy='dynamic', cascade='delete, all')
    highlights = db.relationship('Highlight', backref='user', lazy='dynamic', cascade='delete, all')
    events = db.relationship('Event', backref="user", lazy='dynamic')
    approved_senders = db.relationship('Approved_Sender', backref='user',
                                       lazy='dynamic', cascade='delete, all')
    topics = db.relationship('Topic', backref='user', lazy='dynamic', cascade='delete, all')
    tags = db.relationship('Tag', backref='user', lazy='dynamic', cascade='delete, all')
    tasks = db.relationship('Task', backref='user', lazy='dynamic', cascade='delete, all')
    notifications = db.relationship('Notification', backref='user',
                                    lazy='dynamic', cascade='delete, all')
    suggestion_id = db.Column(db.Integer, db.ForeignKey('suggestion.id'))
    comms = db.relationship("Comms", backref='user', uselist=False)
    
    #########################
    ####    Activity    #####
    ##################3######
    account_created_date = db.Column(db.DateTime, default=datetime.utcnow)
    last_active = db.Column(db.DateTime, default=datetime.utcnow)
    last_action = db.Column(db.String)
    tos = db.Column(db.Boolean, default=False)
    
    ######################
    ####    API??    #####
    ######################
    token = db.Column(db.String(32), index=True, unique=True)
    token_expiration = db.Column(db.DateTime)
    
    ################################
    ####    custom settings    #####
    ################################
    preferences = db.Column(db.String, index=True, default=preferences)
    add_by_email = db.Column(db.String(120), unique=True)
    review_count = db.Column(db.Integer, default=5)
    

    def __repr__(self):
        return '<User {}>'.format(self.email)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            current_app.config['SECRET_KEY'],
            algorithm='HS256').decode('utf-8')

    def get_delete_account_token(self, expires_in=600):
        return jwt.encode(
            {'delete_account': self.id, 'exp': time() + expires_in},
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

    
    @staticmethod
    def verify_delete_account_token(token):
        try:
            id = jwt.decode(token, current_app.config['SECRET_KEY'],
                            algorithms=['HS256'])['delete_account']
        except jwt.exceptions.InvalidTokenError:
            return
        return User.query.get(id)

    @login.user_loader
    def load_user(id):
        return User.query.get(int(id))

    #################################
    # Lurnby add by email functions #
    #################################

    def create_lurnby_email(self):
        letters = string.ascii_lowercase + string.digits
        extra = ''.join(random.choice(letters) for i in range(7))

        return f"{self.email.split('@')[0]}-{extra}@add-article.lurnby.com"

    def set_lurnby_email(self):
        unique = False
        while not unique:
            email = self.create_lurnby_email()
            u = User.query.filter_by(add_by_email=email).first()
            if not u:
                unique = True
        self.add_by_email = email

    #######################
    #     api methods     #
    #######################

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

    #############################
    # Task Queue helper methods #
    #############################

    def launch_task(self, name, description, *args, **kwargs):
        rq_job = current_app.task_queue.enqueue('app.tasks.' + name,
                                                *args, **kwargs, job_timeout=500)
        task = Task(id=rq_job.get_id(), name=name, description=description,
                    user=self)
        db.session.add(task)
        return task

    def get_tasks_in_progress(self):
        return Task.query.filter_by(user=self, complete=False).all()

    def get_task_in_progress(self, name):
        return Task.query.filter_by(name=name, user=self,
                                    complete=False).first()
    #################
    # Notifications #
    #################

    def add_notification(self, name, data):
        self.notifications.filter_by(name=name).delete()
        n = Notification(name=name, payload_json=json.dumps(data), user=self)
        db.session.add(n)
        return n

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    name = db.Column(db.String())
    date = db.Column(db.DateTime())

    """
    Tracked Events

    -> visited platform          //    daily
    -> added article             //    all
    -> added suggested a rticle   //    all
    -> opened article            //    all
    -> added highlight           //    all
    -> exported highlights       //    all
    -> exported all data         //    all
    -> added topic               //    all
    -> reviewed highlights       //    daily
    -> reviewed a highlight      //    all
    -> enabled add by email      //    all
    -> added approved sender     //    all
    -> submitted feedback        //    all
    -> deleted account           //    all
    -> updated user credentials  //    all
    -> updated password          //    all
    -> updated account email     //    all
    -> reset password            //    all
    """
    @staticmethod
    def add(kind, daily=False):
        today_start = datetime(datetime.utcnow().year, datetime.utcnow().month, datetime.utcnow().day, 0, 0)
        today_end = today_start + timedelta(days=1)
        ev = Event.query.filter(Event.name == kind, Event.date >= today_start, Event.date < today_end, Event.user_id==current_user.id).first()
        if not ev:
            ev = Event(user_id=current_user.id, 
                            name=kind,
                            date=datetime.utcnow())
            return ev
        else:
            return False

    def __repr__(self):
        return f'<User {self.user_id} {self.name} on {self.date.strftime("%b %d %Y %H:%M:%S")}>'


class Approved_Sender(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    email = db.Column(db.String(120))

    def __repr__(self):
        return self.email


class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    timestamp = db.Column(db.Float, index=True, default=time)
    payload_json = db.Column(db.Text)

    def get_data(self):
        return json.loads(str(self.payload_json))


class Task(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(128), index=True)
    description = db.Column(db.String(128))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    complete = db.Column(db.Boolean, default=False)

    def get_rq_job(self):
        try:
            rq_job = rq.job.Job.fetch(self.id, connection=current_app.redis)
        except (redis.exceptions.RedisError, rq.exceptions.NoSuchJobError):
            return None
        return rq_job

    def get_progress(self):
        job = self.get_rq_job()
        return job.meta.get('progress', 0) if job is not None else 100


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
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True)
    highlights = db.relationship('Highlight', lazy='dynamic',
                                 backref="article")
    archived = db.Column(db.Boolean, index=True)
    highlightedText = db.Column(db.String, default='')
    tags = db.relationship('Tag', secondary=tags_articles, lazy='dynamic')
    progress = db.Column(db.Float, index=True, default=0.0)
    bookmarks = db.Column(db.String)
    done = db.Column(db.Boolean, default=False)
    notes = db.Column(db.Text, default='')
    article_created_date = db.Column(db.DateTime, default=datetime.utcnow)
    read_time = db.Column(db.String)

    @classmethod
    def return_articles_with_count(cls):
        q_highlights = db.session.query(Article.done, Article.unread,
                                        Article.uuid, Article.title,
                                        Article.progress,
                                        func.count(Highlight.article_id), Article.read_time
                                        ).outerjoin(Article.highlights)\
                                        .group_by(Article.id)\
                                        .filter(Article.user_id == current_user.id,
                                                Article.archived == False)\
                                        .order_by(desc(Article.date_read))
        q_tags = db.session.query(Article.id,
                                  func.count(tags_articles.c.article_id)
                                  ).outerjoin(tags_articles,
                                              tags_articles.c.article_id == Article.id)\
                                  .group_by(Article.id)\
                                  .filter(Article.user_id==current_user.id,
                                          Article.archived==False)\
                                  .order_by(desc(Article.date_read))

        l1 = q_highlights.all()
        l2 = q_tags.all()

        articles = {}
        articles['done'] = []
        articles['unread'] = []
        articles['read'] = []
        articles['recent'] = []

        for i in range(q_highlights.count()):
            y = {}

            if l1[i][0]:
                y['uuid'] = l1[i][2]
                y['title'] = l1[i][3]
                try:
                    y['progress'] = round(l1[i][4])
                except:
                    y['progress'] = 0.0
                y['highlight_count'] = l1[i][5]
                y['read_time'] = l1[i][6]
                y['tag_count'] = l2[i][1]
                articles['done'].append(y)
            elif l1[i][1]:
                y = {}
                y['uuid'] = l1[i][2]
                y['title'] = l1[i][3]
                try:
                    y['progress'] = round(l1[i][4])
                except:
                    y['progress'] = 0.0
                y['highlight_count'] = l1[i][5]
                y['read_time'] = l1[i][6]
                y['tag_count'] = l2[i][1]
                articles['unread'].append(y)
            else:
                y = {}
                y['uuid'] = l1[i][2]
                y['title'] = l1[i][3]
                try:
                    y['progress'] = round(l1[i][4])
                except:
                    y['progress'] = 0.0
                y['highlight_count'] = l1[i][5]
                y['read_time'] = l1[i][6]                
                y['tag_count'] = l2[i][1]
                articles['read'].append(y)

        for i in range(len(articles['read'])):
            if i == 3:
                break
            articles['recent'].append(articles['read'][i])

        return articles

    # return resource for datatable rendering
    def to_table(self):
        return {
            'uuid': self.uuid,
            'title': self.title,
            'progress': self.progress,
            'unread': self.unread,
            'done': self.done,
            'date_read': self.date_read,
            'read_time': self.read_time
        } 


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
    
    def estimated_reading(self):
        soup = BeautifulSoup(self.content, 'html.parser')
        text = soup.find_all(text=True)
        output = ''
        blacklist = [
            '[document]',
            'noscript',
            'header',
            'html',
            'meta',
            'head', 
            'input',
            'script',
            'style',
        ]

        for t in text:
            if t.parent.name not in blacklist and t.string != '\n':
                output += '{} '.format(t)

        word_count = len(output) / 5
        # English wpm read speed https://iovs.arvojournals.org/article.aspx?articleid=2166061#90715174
        slow = 198 
        fast = 258

        low = int(round(word_count / slow))
        high = int(round(word_count / fast))
        high_min = False

        if high >= 60:
            if high % 60 == 0:
                high = f'{high / 60}'
            
            else:
                hrs = high // 60
                minutes = high % 60
                if minutes > 30:
                    hrs += 1
              
                high = f'{hrs}'
        else:
            high = f'{high}'
            high_min = True

        if high_min and low > 60:
            high = f'{high}min'

        if low > 60:
            if low % 60 == 0:
                low = f'{low / 60}h'
            
            else:
                hrs = low // 60
                minutes = low % 60
                if minutes > 30:
                    hrs += 1
              
                low = f'{hrs}h'
        else:
            low = f'{low}min'

        self.read_time = (f'{high}-{low} read')

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
              nullable=False, primary_key=True, index=True),
    db.Column('topic_id', db.Integer, db.ForeignKey('topic.id'),
              nullable=False, primary_key=True, index=True)
)


tags_highlights = db.Table(
    'tags_highlights',
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), nullable=False, index=True),
    db.Column('highlight_id', db.Integer, db.ForeignKey('highlight.id'), index=True,
              nullable=False)
)


class Suggestion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String)
    title = db.Column(db.String)
    summary = db.Column(db.String)
    users = db.relationship('User', backref='suggestion', lazy='dynamic')

    def __repr__(self):
        return f'<{self.title}: Users: {self.users.count()}>'

    @classmethod
    def get_random(cls):
        x = Suggestion.query.order_by(func.random()).first()
        
        return x

class Highlight(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String)  # should I set a max length?
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'),index=True)
    article_id = db.Column(db.Integer, db.ForeignKey('article.id'), index=True)
    topics = db.relationship(
        'Topic', secondary=highlights_topics, lazy='dynamic')
    
    archived = db.Column(db.Boolean, index=True)
    no_topics = db.Column(db.Boolean, default=True, index=True)
    note = db.Column(db.String, index=True)
    tags = db.relationship('Tag', secondary=tags_highlights, lazy='dynamic')
    position = db.Column(db.String)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    review_date = db.Column(db.DateTime, default=datetime.utcnow)
    review_schedule = db.Column(db.Integer, default=0)
    do_not_review = db.Column(db.Boolean, default=False)

    # add highlight to topic
    def AddToTopic(self, topic):
        if not self.is_added_topic(topic) and topic.user_id == self.user_id:
            self.topics.append(topic)

    # remove highlight from topic
    def RemoveFromTopic(self, topic):
        if self.is_added_topic(topic) and topic.user_id == self.user_id:
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
                    user_id=user.id, archived=False).order_by(Topic.last_used.desc()).all()

        return q

    # add highlight to tag
    def AddToTag(self, tag):
        if not self.is_added_tag(tag) and tag.user_id == self.user_id:
            self.tags.append(tag)

    # remove highlight from tag
    def RemoveFromTag(self, tag):
        if self.is_added_tag(tag) and tag.user_id == self.user_id:
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
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True)
    highlights = db.relationship(
        'Highlight', secondary=highlights_topics, lazy='dynamic')
    archived = db.Column(db.Boolean, index=True)
    tags = db.relationship('Tag', secondary=tags_topics, lazy='dynamic')
    last_used = db.Column(db.DateTime, default=datetime.utcnow)

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
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True)
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


def update_user_last_action(action):
    if current_user:
        print(f'last action = {action}')
        db.session.execute(
            User.__table__.
            update().
            values(last_action=action).
            where(User.id == current_user.id))


def after_insert_listener(mapper, connection, target):
    # 'target' is the inserted object
    if isinstance(target, Highlight):
        update_user_last_action('added highlight')
    elif isinstance(target, Article):
        update_user_last_action('added article')
    elif isinstance(target, Tag):
        update_user_last_action('added tag')
    elif isinstance(target, Topic):
        update_user_last_action('added topic')
    


def after_update_listener(mapper, connection, target):
    # 'target' is the inserted object
    if isinstance(target, Highlight):
        update_user_last_action('updated highlight')
    elif isinstance(target, Article):
        update_user_last_action('updated article')
    elif isinstance(target, Tag):
        update_user_last_action('updated tag')
    elif isinstance(target, Topic):
        update_user_last_action('updated topic')


db.event.listen(Article, 'after_insert', after_insert_listener)
db.event.listen(Highlight, 'after_insert', after_insert_listener)
db.event.listen(Topic, 'after_insert', after_insert_listener)
db.event.listen(Tag, 'after_insert', after_insert_listener)
db.event.listen(Task, 'after_insert', after_insert_listener)


# db.event.listen(Article, 'after_update', after_update_listener)
# db.event.listen(Highlight, 'after_update', after_update_listener)
db.event.listen(Topic, 'after_update', after_update_listener)
# db.event.listen(Tag, 'after_update', after_update_listener)


def receive_team_users_append(target, value, initiator):
    update_user_last_action('added/removed highlight from topic')


db.event.listen(Highlight.topics, 'append', receive_team_users_append)
db.event.listen(Highlight.topics, 'remove', receive_team_users_append)
