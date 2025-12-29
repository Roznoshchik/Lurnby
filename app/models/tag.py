from sqlalchemy import func

from app.models.base import db, generate_str_id
from app.models.article import tags_articles
from app.models.highlight import tags_highlights
from app.models.topic import tags_topics


class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String, default=generate_str_id)
    name = db.Column(db.String(128), index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), index=True)
    archived = db.Column(db.Boolean, index=True, default=False)
    goal = db.Column(db.String(512))
    highlight_count = db.Column(db.Integer, default=0)
    article_count = db.Column(db.Integer, default=0)

    articles = db.relationship("Article", secondary=tags_articles, back_populates="tags", lazy="dynamic")

    highlights = db.relationship("Highlight", secondary=tags_highlights, back_populates="tags", lazy="dynamic")

    topics = db.relationship("Topic", secondary=tags_topics, back_populates="tags", lazy="dynamic")

    @property
    def fields_that_can_be_updated(self):
        return ["name", "archived"]

    def is_added_highlight(self, highlight):
        h_id = tags_highlights.c.highlight_id
        return self.highlights.filter(highlight.id == h_id).count() > 0

    def is_added_topic(self, topic):
        return self.topics.filter(topic.id == tags_topics.c.topic_id).count() > 0

    def is_added_article(self, article):
        return self.articles.filter(article.id == tags_articles.c.article_id).count() > 0

    def __repr__(self) -> str:
        return f"{self.id}: {self.name}"

    def to_dict(self):
        return {
            "id": self.id,
            "uuid": self.uuid,
            "user_id": self.user_id,
            "name": self.name,
            "archived": self.archived,
            "highlight_count": self.highlight_count,
            "article_count": self.article_count,
        }

    @staticmethod
    def query_with_count(user):
        from app.models.article import Article

        query = (
            db.session.query(Tag, Article.archived, func.count("*"))
            .outerjoin(tags_articles, tags_articles.c.tag_id == Tag.id)
            .outerjoin(Article, tags_articles.c.article_id == Article.id)
            .filter(Tag.user_id == user.id, Tag.archived == False)  # noqa: E712
            .group_by(Tag.id, Article.archived)
        )

        dedupe = {}
        for row in query:
            tag = row[0]
            is_archived = row[1]
            article_count = row[2]

            if tag.id in dedupe:
                if is_archived is None or is_archived is True:
                    continue
                else:
                    dedupe[tag.id]["count"] += article_count
            else:
                dedupe[tag.id] = {"tag": tag}
                if is_archived is False:
                    dedupe[tag.id]["count"] = article_count
                else:
                    dedupe[tag.id]["count"] = 0

        res = list(dedupe.values())
        return res
