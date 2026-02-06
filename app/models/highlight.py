import random
import re
from datetime import datetime

from bs4 import BeautifulSoup
import sqlalchemy as sa
import sqlalchemy.orm as so

from app.models.base import db, generate_str_id
from app.models.associations import highlights_topics, tags_highlights
from app.models.tag import Tag


class Highlight(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    uuid: so.Mapped[str] = so.mapped_column(sa.String, default=generate_str_id, unique=True)
    text: so.Mapped[str | None] = so.mapped_column(sa.String)
    prompt: so.Mapped[str | None] = so.mapped_column(sa.String)
    source: so.Mapped[str | None] = so.mapped_column(sa.String)
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey("user.id"), index=True)
    article_id: so.Mapped[int | None] = so.mapped_column(sa.ForeignKey("article.id"), index=True)
    topics = db.relationship(
        "Topic",
        secondary=highlights_topics,
        back_populates="highlights",
        lazy="dynamic",
    )

    archived: so.Mapped[bool] = so.mapped_column(sa.Boolean, index=True, default=False)
    no_topics: so.Mapped[bool] = so.mapped_column(sa.Boolean, default=True, index=True)
    note: so.Mapped[str | None] = so.mapped_column(sa.String, index=True)
    tags = db.relationship("Tag", secondary=tags_highlights, back_populates="highlights")
    start_chunk: so.Mapped[int | None] = so.mapped_column(sa.Integer)
    start: so.Mapped[int | None] = so.mapped_column(sa.Integer)
    end_chunk: so.Mapped[int | None] = so.mapped_column(sa.Integer)
    end: so.Mapped[int | None] = so.mapped_column(sa.Integer)
    created_date: so.Mapped[datetime] = so.mapped_column(sa.DateTime, default=datetime.utcnow)
    review_date: so.Mapped[datetime] = so.mapped_column(sa.DateTime, default=datetime.utcnow)
    review_schedule: so.Mapped[int] = so.mapped_column(sa.Integer, default=0)
    do_not_review: so.Mapped[bool] = so.mapped_column(sa.Boolean, default=False)

    def __repr__(self):
        arch = " ARCHIVED" if self.archived else ""
        return f"<Highlight {self.id}: chunk[{self.start_chunk}:{self.start}]-[{self.end_chunk}:{self.end}]{arch}>"

    def to_dict(self):
        source = self.article.source or self.article.source_url if self.article else "unknown"

        return {
            "id": self.id,
            "uuid": self.uuid,
            "source": source,
            "text": self.text,
            "note": self.note,
            "prompt": self.prompt,
            "article_id": self.article_id,
            "article_title": self.article.title if self.article else None,
            "article_uuid": self.article.uuid if self.article else None,
            "user_id": self.user_id,
            "start_chunk": self.start_chunk,
            "start": self.start,
            "end_chunk": self.end_chunk,
            "end": self.end,
            "created_date": self.created_date,
            "review_date": self.review_date,
            "review_schedule": self.review_schedule,
            "do_not_review": self.do_not_review,
            "archived": self.archived,
            "tags": [tag.to_dict() for tag in self.tags],
        }

    @property
    def tag_list(self):
        return [tag.name for tag in self.tags]

    @property
    def tag_ids(self):
        """Get tag IDs efficiently from junction table without loading Tag objects."""
        return db.session.scalars(
            sa.select(tags_highlights.c.tag_id).where(tags_highlights.c.highlight_id == self.id)
        ).all()

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
            # Dual-write: also add to corresponding Tag
            tag = self._get_or_create_tag_for_topic(topic)
            if tag:
                self.add_tag(tag)

    def add_tag(self, tag):
        if not self.is_tagged_with(tag) and tag.user_id == self.user_id:
            self.tags.append(tag)
            tag.highlight_count += 1

    def remove_tag(self, tag):
        if self.is_tagged_with(tag):
            self.tags.remove(tag)
            tag.highlight_count -= 1

    def RemoveFromTopic(self, topic):
        if self.is_added_topic(topic) and topic.user_id == self.user_id:
            self.topics.remove(topic)
            if self.topics.count() == 0:
                self.no_topics = True
            # Dual-write: also remove from corresponding Tag
            tag = self._get_tag_for_topic(topic)
            if tag:
                self.remove_tag(tag)

    def is_added_topic(self, topic):
        return self.topics.filter(topic.id == highlights_topics.c.topic_id).count() > 0

    def _get_or_create_tag_for_topic(self, topic):
        """Get or create a Tag matching a Topic by normalized name."""
        normalized_name = topic.title.strip().lower()
        stmt = sa.select(Tag).where(
            Tag.user_id == topic.user_id, sa.func.lower(sa.func.trim(Tag.name)) == normalized_name
        )
        tag = db.session.scalar(stmt)

        if not tag:
            tag = Tag(
                user_id=topic.user_id,
                name=topic.title.strip(),
                archived=topic.archived or False,
                last_used=topic.last_used,
            )
            db.session.add(tag)

        return tag

    def _get_tag_for_topic(self, topic):
        """Get the Tag matching a Topic by normalized name (don't create)."""
        normalized_name = topic.title.strip().lower()
        stmt = sa.select(Tag).where(
            Tag.user_id == topic.user_id, sa.func.lower(sa.func.trim(Tag.name)) == normalized_name
        )
        return db.session.scalar(stmt)

    def is_added_tag(self, tag):
        return tag in self.tags

    def is_tagged_with(self, tag):
        return tag in self.tags

    def not_added_topic(self):

        query = db.session.query(highlights_topics).filter(highlights_topics.c.highlight_id == self.id).count()

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
        q = db.session.query(Tag).filter(~Tag.id.in_(sub)).filter_by(user_id=user.id, archived=False).all()

        return q
