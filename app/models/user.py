import base64
import os
import random
import string
from datetime import datetime, timedelta
from time import time

import jwt
from flask import current_app, url_for
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app.models.base import db, login, CustomLogger, redis, rq, generate_str_id


logger = CustomLogger("MODELS")
PREFERENCES = '{"font": "sans-serif","color": "light-mode", \
              "size": "4","spacing": "line-height-min"}'


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
    articles = db.relationship(
        "Article", backref="user", lazy="dynamic", cascade="delete, all"
    )
    highlights = db.relationship(
        "Highlight", backref="user", lazy="dynamic", cascade="delete, all"
    )
    events = db.relationship("Event", backref="user", lazy="dynamic")

    approved_senders = db.relationship(
        "Approved_Sender", backref="user", lazy="dynamic", cascade="delete, all"
    )
    topics = db.relationship(
        "Topic", backref="user", lazy="dynamic", cascade="delete, all"
    )
    tags = db.relationship("Tag", backref="user", lazy="dynamic", cascade="delete, all")
    tasks = db.relationship(
        "Task",
        backref="user",
        cascade_backrefs=False,
        lazy="dynamic",
        cascade="delete, all",
    )
    notifications = db.relationship(
        "Notification", backref="user", lazy="dynamic", cascade="delete, all"
    )
    suggestion_id = db.Column(db.Integer, db.ForeignKey("suggestion.id"))
    comms = db.relationship("Comms", backref="user", uselist=False)

    #########################
    ####    Activity    #####
    #########################
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
    preferences = db.Column(db.String, index=True, default=PREFERENCES)
    add_by_email = db.Column(db.String(120), unique=True)
    review_count = db.Column(db.Integer, default=5)

    @property
    def fields_that_can_be_updated(self):
        return ["preferences", "review_count", "tos", "firstname", "username", "email"]

    def __repr__(self):
        return "<User {}>".format(self.email)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {"reset_password": self.id, "exp": time() + expires_in},
            current_app.config["SECRET_KEY"],
            algorithm="HS256",
        )

    def get_delete_account_token(self, expires_in=600):
        return jwt.encode(
            {"delete_account": self.id, "exp": time() + expires_in},
            current_app.config["SECRET_KEY"],
            algorithm="HS256",
        )

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(
                token, current_app.config["SECRET_KEY"], algorithms=["HS256"]
            )["reset_password"]
        except jwt.exceptions.InvalidTokenError:
            return
        return User.query.get(id)

    @staticmethod
    def verify_delete_account_token(token):
        try:
            id = jwt.decode(
                token, current_app.config["SECRET_KEY"], algorithms=["HS256"]
            )["delete_account"]
        except jwt.exceptions.InvalidTokenError:
            return
        return User.query.get(id)

    #################################
    # Lurnby add by email functions #
    #################################

    def create_lurnby_email(self):
        letters = string.ascii_lowercase + string.digits
        extra = "".join(random.choice(letters) for i in range(7))
        if current_app.config["DEV"]:
            return f"{self.email.split('@')[0]}-{extra}@add-article-staging.lurnby.com"

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

    def get_tags_dict(self):
        tags = self.tags.filter_by(archived=False).all()
        tag_names = []
        for tag in tags:
            tag_names.append(tag.name)

        data = {
            "id": self.id,
            "tags": tag_names,
            "_links": {
                "self": url_for("api.legacy_get_user_tags", id=self.id),
                "articles": url_for("api.legacy_add_article", id=self.id),
            },
        }
        return data

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "firstname": self.firstname,
            "articles_count": self.articles.count(),
            "highlights_count": self.highlights.count(),
            "admin": self.admin,
            "review_count": self.review_count,
            "add_by_email": self.add_by_email,
            "preferences": self.preferences,
            "tos": self.tos,
        }

    def from_dict(self, data):
        for field in ["username", "email"]:
            setattr(self, field, data[field])
        self.set_password(data["password"])

    def get_token(self, expires_in=2592000):
        now = datetime.utcnow()
        if self.token and self.token_expiration > now + timedelta(seconds=60):
            return self.token
        self.token = base64.b64encode(os.urandom(24)).decode("utf-8")
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

    def launch_task(self, name, description="", *args, **kwargs):
        from app.models.task import Task
        try:
            logger.info(f"Starting task: {name} for user {self.id}")
            if not os.environ.get("testing"):
                rq_job = current_app.task_queue.enqueue(
                    "app.tasks." + name, *args, **kwargs, job_timeout=500
                )
                id = rq_job.get_id()
                task = Task(id=id, name=name, description=description, user=self)
                db.session.add(task)
                return task
            else:
                raise redis.exceptions.ConnectionError
        except redis.exceptions.ConnectionError:
            logger.error("Error connecting to Redis")
            import app.tasks as app_tasks

            func = getattr(app_tasks, name)
            func(*args, **kwargs)

            task = Task(
                id=generate_str_id(), name=name, description=description, user=self
            )
            db.session.add(task)
            return task

    def get_tasks_in_progress(self):
        from app.models.task import Task
        return Task.query.filter_by(user=self, complete=False).all()

    def get_task_in_progress(self, name):
        from app.models.task import Task
        return Task.query.filter_by(name=name, user=self, complete=False).first()

    #################
    # Notifications #
    #################

    def add_notification(self, name, data):
        from app.models.notification import Notification
        import json
        self.notifications.filter_by(name=name).delete()
        n = Notification(name=name, payload_json=json.dumps(data), user=self)
        db.session.add(n)
        return n

    ##########################
    #     review methods     #
    ##########################
    def get_highlights_for_review(self, tag_ids, per_tier):
        from app.models.highlight import Highlight
        from app.models.tag import tags_highlights

        if not per_tier:
            per_tier = self.review_count

        join_highlight_id = tags_highlights.c.highlight_id
        join_tag_id = tags_highlights.c.tag_id

        highlights = self.highlights.filter_by(archived=False, do_not_review=False)

        if tag_ids:
            highlights = highlights.join(
                tags_highlights, join_highlight_id == Highlight.id
            ).filter(join_tag_id.in_(tag_ids))

        return self.get_highlights_by_tier(highlights, per_tier)

    def get_highlights_by_tier(self, highlights, per_tier):
        from app.models.highlight import Highlight

        today = datetime.today()

        tier0 = highlights.filter(Highlight.review_schedule == 0)
        tier1 = highlights.filter(Highlight.review_schedule == 1)
        tier2 = highlights.filter(Highlight.review_schedule == 2)
        tier3 = highlights.filter(Highlight.review_schedule == 3)
        tier4 = highlights.filter(Highlight.review_schedule == 4)
        tier5 = highlights.filter(Highlight.review_schedule == 5)
        tier6 = highlights.filter(Highlight.review_schedule == 6)
        tier7 = highlights.filter(Highlight.review_schedule == 7)

        tier0 = [
            highlight.to_dict()
            for highlight in tier0.filter(
                Highlight.review_date < today - timedelta(days=1)
            )
            .limit(per_tier)
            .all()
        ]
        tier1 = [
            highlight.to_dict()
            for highlight in tier1.filter(
                Highlight.review_date < today - timedelta(days=3)
            )
            .limit(per_tier)
            .all()
        ]
        tier2 = [
            highlight.to_dict()
            for highlight in tier2.filter(
                Highlight.review_date < today - timedelta(days=7)
            )
            .limit(per_tier)
            .all()
        ]
        tier3 = [
            highlight.to_dict()
            for highlight in tier3.filter(
                Highlight.review_date < today - timedelta(days=14)
            )
            .limit(per_tier)
            .all()
        ]
        tier4 = [
            highlight.to_dict()
            for highlight in tier4.filter(
                Highlight.review_date < today - timedelta(days=30)
            )
            .limit(per_tier)
            .all()
        ]
        tier5 = [
            highlight.to_dict()
            for highlight in tier5.filter(
                Highlight.review_date < today - timedelta(days=90)
            )
            .limit(per_tier)
            .all()
        ]
        tier6 = [
            highlight.to_dict()
            for highlight in tier6.filter(
                Highlight.review_date < today - timedelta(days=180)
            )
            .limit(per_tier)
            .all()
        ]
        tier7 = [
            highlight.to_dict()
            for highlight in tier7.filter(
                Highlight.review_date < today - timedelta(days=365)
            )
            .limit(per_tier)
            .all()
        ]

        return {
            "tier0": tier0,
            "tier1": tier1,
            "tier2": tier2,
            "tier3": tier3,
            "tier4": tier4,
            "tier5": tier5,
            "tier6": tier6,
            "tier7": tier7,
        }


@login.user_loader
def load_user(id):
    return User.query.get(int(id))
