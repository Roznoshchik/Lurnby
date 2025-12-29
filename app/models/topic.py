from datetime import datetime

from sqlalchemy import func

from app.models.base import db
from app.models.highlight import highlights_topics


tags_topics = db.Table(
    "tags_topics",
    db.Column("tag_id", db.Integer, db.ForeignKey("tag.id"), nullable=False),
    db.Column("topic_id", db.Integer, db.ForeignKey("topic.id"), nullable=False),
)


class Topic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(512), index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), index=True)
    highlights = db.relationship(
        "Highlight",
        secondary=highlights_topics,
        back_populates="topics",
        lazy="dynamic",
    )
    archived = db.Column(db.Boolean, index=True)
    tags = db.relationship("Tag", secondary=tags_topics, back_populates="topics", lazy="dynamic")
    last_used = db.Column(db.DateTime, default=datetime.utcnow)

    def is_added_highlight(self, highlight):
        h_id = highlights_topics.c.highlight_id
        return self.highlights.filter(highlight.id == h_id).count() > 0

    def add_tag(self, tag):
        if not self.is_added_tag(tag):
            self.tags.append(tag)

    def remove_tag(self, tag):
        if self.is_added_tag(tag):
            self.tags.remove(tag)

    def is_added_tag(self, tag):
        return self.tags.filter(tag.id == tags_topics.c.tag_id).count() > 0

    def not_added_tag(self):

        query = db.session.query(tags_topics).filter(tags_topics.c.topic_id == self.id).count()

        if query == 0:
            return True
        else:
            return False

    def not_in_tags(self, user):
        from app.models.tag import Tag

        sub = (
            db.session.query(Tag.id)
            .outerjoin(tags_topics, tags_topics.c.tag_id == Tag.id)
            .filter(tags_topics.c.topic_id == self.id)
        )
        q = db.session.query(Tag).filter(~Tag.id.in_(sub)).filter_by(user_id=user.id).all()

        return q

    @staticmethod
    def query_with_count(user):
        from app.models.highlight import Highlight

        q = (
            db.session.query(Topic, Highlight.archived, func.count("*"))
            .outerjoin(highlights_topics, highlights_topics.c.topic_id == Topic.id)
            .outerjoin(Highlight, highlights_topics.c.highlight_id == Highlight.id)
            .filter(Topic.user_id == user.id, Topic.archived == False)  # noqa E712
            .group_by(Topic.id, Highlight.archived)
        )

        dedupe = {}
        for row in q:
            if row[0].id in dedupe:
                if row[1] is None or row[1] is True:
                    continue
                else:
                    dedupe[row[0].id]["count"] += row[2]
            else:
                dedupe[row[0].id] = {"tag": row[0]}
                if row[1] is False:
                    dedupe[row[0].id]["count"] = row[2]
                else:
                    dedupe[row[0].id]["count"] = 0

        res = []
        for k, v in dedupe.items():
            res.append(v)

        return res
