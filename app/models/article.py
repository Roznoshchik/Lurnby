from datetime import datetime

from bs4 import BeautifulSoup
from flask import url_for
from flask_login import current_user
from sqlalchemy import desc, func, Index
from sqlalchemy_utils import UUIDType
import uuid

from app.models.base import db


tags_articles = db.Table(
    "tags_articles",
    db.Column("tag_id", db.Integer, db.ForeignKey("tag.id"), nullable=False),
    db.Column("article_id", db.Integer, db.ForeignKey("article.id"), nullable=False),
)


class Article(db.Model):
    __mapper_args__ = {"confirm_deleted_rows": False}

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(UUIDType(), default=uuid.uuid4, index=True, unique=True)
    unread = db.Column(db.Boolean, index=True, default=True)
    title = db.Column(db.String(255), default="Something went wrong", index=True)
    filetype = db.Column(db.String(32))
    source = db.Column(db.String(500))
    source_url = db.Column(db.String(500))
    content = db.Column(db.Text)
    date_read = db.Column(db.DateTime, default=datetime.utcnow)
    date_read_date = db.Column(db.Date)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), index=True)
    highlights = db.relationship("Highlight", lazy="dynamic", backref="article")
    archived = db.Column(db.Boolean, index=True, default=False)
    highlightedText = db.Column(db.String, default="")
    tags = db.relationship(
        "Tag", secondary=tags_articles, back_populates="articles", lazy="dynamic"
    )
    progress = db.Column(db.Float, index=True, default=0.0)
    bookmarks = db.Column(db.String)
    done = db.Column(db.Boolean, default=False)
    notes = db.Column(db.Text, default="")
    reflections = db.Column(db.Text, default="")

    article_created_date = db.Column(db.DateTime, default=datetime.utcnow)
    read_time = db.Column(db.String)
    processing = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f"<{self.id}: {self.title}>"

    @property
    def fields_that_can_be_updated(self):
        return [
            "done",
            "unread",
            "archived",
            "date_read",
            "progress",
            "bookmarks",
            "source",
            "title",
            "content",
            "notes",
            "reflections",
        ]

    @property
    def tag_list(self):
        return [tag.name for tag in self.tags.all()]

    @classmethod
    def return_articles_with_count(cls):
        from app.models.highlight import Highlight

        q_highlights = (
            db.session.query(
                Article.done,
                Article.unread,
                Article.uuid,
                Article.title,
                Article.progress,
                func.count(Highlight.article_id),
                Article.read_time,
            )
            .outerjoin(Article.highlights)
            .group_by(Article.id)
            .filter(Article.user_id == current_user.id, Article.archived is False)
            .order_by(desc(Article.date_read))
        )
        q_tags = (
            db.session.query(Article.id, func.count(tags_articles.c.article_id))
            .outerjoin(tags_articles, tags_articles.c.article_id == Article.id)
            .group_by(Article.id)
            .filter(Article.user_id == current_user.id, Article.archived is False)
            .order_by(desc(Article.date_read))
        )

        l1 = q_highlights.all()
        l2 = q_tags.all()

        articles = {}
        articles["done"] = []
        articles["unread"] = []
        articles["read"] = []
        articles["recent"] = []

        for i in range(q_highlights.count()):
            y = {}

            if l1[i][0]:
                y["uuid"] = l1[i][2]
                y["title"] = l1[i][3]
                try:
                    y["progress"] = round(l1[i][4])
                except Exception:
                    y["progress"] = 0.0
                y["highlight_count"] = l1[i][5]
                y["read_time"] = l1[i][6]
                y["tag_count"] = l2[i][1]
                articles["done"].append(y)
            elif l1[i][1]:
                y = {}
                y["uuid"] = l1[i][2]
                y["title"] = l1[i][3]
                try:
                    y["progress"] = round(l1[i][4])
                except Exception:
                    y["progress"] = 0.0
                y["highlight_count"] = l1[i][5]
                y["read_time"] = l1[i][6]
                y["tag_count"] = l2[i][1]
                articles["unread"].append(y)
            else:
                y = {}
                y["uuid"] = l1[i][2]
                y["title"] = l1[i][3]
                try:
                    y["progress"] = round(l1[i][4])
                except Exception:
                    y["progress"] = 0.0
                y["highlight_count"] = l1[i][5]
                y["read_time"] = l1[i][6]
                y["tag_count"] = l2[i][1]
                articles["read"].append(y)

        for i in range(len(articles["read"])):
            if i == 3:
                break
            articles["recent"].append(articles["read"][i])

        return articles

    def to_legacy_dict(self):
        data = {
            "article_id": self.id,
            "_links": {
                "self": url_for("api.add_article", id=self.id),
                "tags": url_for("api.legacy_get_user_tags", id=self.id),
            },
        }
        return data

    def to_dict(self, preview=True):
        data = {
            "_id": self.id,
            "id": str(self.uuid),
            "user_id": self.user_id,
            "source": self.source or self.source_url,
            "source_url": self.source_url,
            "title": self.title,
            "content": self.content if not preview else None,
            "unread": self.unread,
            "archived": self.archived,
            "done": self.done,
            "date_read": self.date_read,
            "notes": self.notes if not preview else None,
            "reflections": self.reflections if not preview else None,
            "read_time": self.read_time,
            "progress": self.progress,
            "created_at": self.article_created_date,
            "highlights_count": self.highlights.count(),
            "tags": [
                tag.to_dict() for tag in self.tags.all()
            ],
        }
        return data

    def estimated_reading(self):
        soup = BeautifulSoup(self.content or "", "html.parser")
        text = soup.find_all(string=True)
        output = ""
        blacklist = [
            "[document]",
            "noscript",
            "header",
            "html",
            "meta",
            "head",
            "input",
            "script",
            "style",
        ]

        for t in text:
            if t.parent.name not in blacklist and t.string != "\n":
                output += f"{t} "

        word_count = len(output) / 5
        slow = 198
        fast = 258

        low = int(round(word_count / slow))
        high = int(round(word_count / fast))
        high_min = False

        if high >= 60:
            if high % 60 == 0:
                high = f"{high / 60}"

            else:
                hrs = high // 60
                minutes = high % 60
                if minutes > 30:
                    hrs += 1

                high = f"{hrs}"
        else:
            high = f"{high}"
            high_min = True

        if high_min and low > 60:
            high = f"{high}min"

        if low > 60:
            if low % 60 == 0:
                low = f"{low / 60}h"

            else:
                hrs = low // 60
                minutes = low % 60
                if minutes > 30:
                    hrs += 1

                low = f"{hrs}h"
        else:
            low = f"{low}min"

        self.read_time = f"{high}-{low} read"

    def add_tag(self, tag):
        if not self.is_added_tag(tag):
            self.tags.append(tag)
            tag.article_count += 1
            for h in self.highlights:
                tag.highlight_count += 1
                h.add_tag(tag)

    def remove_tag(self, tag):
        if self.is_added_tag(tag):
            self.tags.remove(tag)
            tag.article_count -= 1
            for h in self.highlights:
                tag.highlight_count -= 1
                h.remove_tag(tag)

    def is_added_tag(self, tag):
        return self.tags.filter(tag.id == tags_articles.c.tag_id).count() > 0

    def not_added_tag(self):
        t_aid = tags_articles.c.article_id
        query = db.session.query(tags_articles).filter(t_aid == self.id).count()

        if query == 0:
            return True
        else:
            return False

    def not_in_tags(self, user):
        from app.models.tag import Tag

        sub = (
            db.session.query(Tag.id)
            .outerjoin(tags_articles, tags_articles.c.tag_id == Tag.id)
            .filter(tags_articles.c.article_id == self.id)
        )

        q = (
            db.session.query(Tag)
            .filter(~Tag.id.in_(sub))
            .filter_by(user_id=user.id, archived=False)
            .all()
        )

        return q


articles_lower_title_key = Index("articles_lower_title_key", func.lower(Article.title))
