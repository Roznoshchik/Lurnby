import random
import re
from datetime import datetime

from bs4 import BeautifulSoup

from app.models.base import db, generate_str_id


highlights_topics = db.Table(
    "highlights_topics",
    db.Column(
        "highlight_id",
        db.Integer,
        db.ForeignKey("highlight.id"),
        nullable=False,
        primary_key=True,
        index=True,
    ),
    db.Column(
        "topic_id",
        db.Integer,
        db.ForeignKey("topic.id"),
        nullable=False,
        primary_key=True,
        index=True,
    ),
)

tags_highlights = db.Table(
    "tags_highlights",
    db.Column(
        "tag_id", db.Integer, db.ForeignKey("tag.id"), nullable=False, index=True
    ),
    db.Column(
        "highlight_id",
        db.Integer,
        db.ForeignKey("highlight.id"),
        index=True,
        nullable=False,
    ),
)


class Highlight(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String, default=generate_str_id, unique=True)
    text = db.Column(db.String)
    prompt = db.Column(db.String)
    source = db.Column(db.String)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), index=True)
    article_id = db.Column(db.Integer, db.ForeignKey("article.id"), index=True)
    topics = db.relationship(
        "Topic",
        secondary=highlights_topics,
        back_populates="highlights",
        lazy="dynamic",
    )

    archived = db.Column(db.Boolean, index=True, default=False)
    no_topics = db.Column(db.Boolean, default=True, index=True)
    untagged = db.Column(db.Boolean, default=True)
    note = db.Column(db.String, index=True)
    tags = db.relationship(
        "Tag", secondary=tags_highlights, back_populates="highlights", lazy="dynamic"
    )
    position = db.Column(db.String)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    review_date = db.Column(db.DateTime, default=datetime.utcnow)
    review_schedule = db.Column(db.Integer, default=0)
    do_not_review = db.Column(db.Boolean, default=False)

    def to_dict(self):
        source = self.source or (self.article.title if self.article else "unknown")

        return {
            "id": self.id,
            "uuid": self.uuid,
            "source": source,
            "text": self.text,
            "note": self.note,
            "prompt": self.prompt,
            "article_id": self.article_id,
            "user_id": self.user_id,
            "created_date": self.created_date,
            "review_date": self.review_date,
            "review_schedule": self.review_schedule,
            "do_not_review": self.do_not_review,
            "archived": self.archived,
            "untagged": self.untagged,
            "tags": [tag.to_dict() for tag in self.tags.all()],
        }

    @property
    def tag_list(self):
        return [tag.name for tag in self.tags.all()]

    @property
    def fields_that_can_be_updated(self):
        return [
            "source",
            "text",
            "note",
            "prompt",
            "review_date",
            "review_schedule",
            "do_not_review",
            "archived",
        ]

    def create_prompt(self):
        soup = BeautifulSoup(self.text, features="lxml")
        for text in soup.find_all(string=True):
            words = text.split(" ")
            if len(words) > 3:
                for i in range(0, len(words) // 3):
                    num = random.randint(0, len(words) - 1)
                    words[num] = re.sub(r"[\w\d]+", "_____", words[num])
            text.replace_with(" ".join(words))

        return soup.prettify()

    def AddToTopic(self, topic):
        if not self.is_added_topic(topic) and topic.user_id == self.user_id:
            self.topics.append(topic)
            self.no_topics = True

    def add_tag(self, tag):
        if not self.is_tagged_with(tag) and tag.user_id == self.user_id:
            self.tags.append(tag)
            self.untagged = False
            tag.highlight_count += 1

    def remove_tag(self, tag):
        if self.is_tagged_with(tag):
            self.tags.remove(tag)
            tag.highlight_count -= 1
            if self.tags.count() == 0:
                self.untagged = True

    def RemoveFromTopic(self, topic):
        if self.is_added_topic(topic) and topic.user_id == self.user_id:
            self.topics.remove(topic)
            if self.topics.count() == 0:
                self.no_topics = True

    def is_added_topic(self, topic):
        return self.topics.filter(topic.id == highlights_topics.c.topic_id).count() > 0

    def is_added_tag(self, tag):
        return self.tags.filter(tag.id == tags_highlights.c.tag_id).count() > 0

    def is_tagged_with(self, tag):
        return self.tags.filter(tag.id == tags_highlights.c.tag_id).count() > 0

    def not_added_topic(self):

        query = (
            db.session.query(highlights_topics)
            .filter(highlights_topics.c.highlight_id == self.id)
            .count()
        )

        if query == 0:
            return True
        else:
            return False

    def not_in_topics(self, user):
        from app.models.topic import Topic

        sub = (
            db.session.query(Topic.id)
            .outerjoin(highlights_topics, highlights_topics.c.topic_id == Topic.id)
            .filter(highlights_topics.c.highlight_id == self.id)
        )
        q = (
            db.session.query(Topic)
            .filter(~Topic.id.in_(sub))
            .filter_by(user_id=user.id, archived=False)
            .order_by(Topic.last_used.desc())
            .all()
        )

        return q

    def not_in_tags(self, user):
        from app.models.tag import Tag

        sub = (
            db.session.query(Tag.id)
            .outerjoin(tags_highlights, tags_highlights.c.tag_id == Tag.id)
            .filter(tags_highlights.c.highlight_id == self.id)
        )
        q = (
            db.session.query(Tag)
            .filter(~Tag.id.in_(sub))
            .filter_by(user_id=user.id, archived=False)
            .all()
        )

        return q
