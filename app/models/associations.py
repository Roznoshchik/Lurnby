"""Association tables for many-to-many relationships."""

import sqlalchemy as sa

from app.models.base import db


highlights_topics = sa.Table(
    "highlights_topics",
    db.metadata,
    sa.Column("highlight_id", sa.Integer, sa.ForeignKey("highlight.id"), primary_key=True, nullable=False, index=True),
    sa.Column("topic_id", sa.Integer, sa.ForeignKey("topic.id"), primary_key=True, nullable=False),
)

tags_highlights = sa.Table(
    "tags_highlights",
    db.metadata,
    sa.Column("tag_id", sa.Integer, sa.ForeignKey("tag.id"), primary_key=True, nullable=False),
    sa.Column("highlight_id", sa.Integer, sa.ForeignKey("highlight.id"), primary_key=True, nullable=False, index=True),
)

tags_articles = sa.Table(
    "tags_articles",
    db.metadata,
    sa.Column("tag_id", sa.Integer, sa.ForeignKey("tag.id"), primary_key=True, nullable=False),
    sa.Column("article_id", sa.Integer, sa.ForeignKey("article.id"), primary_key=True, nullable=False, index=True),
)

tags_topics = sa.Table(
    "tags_topics",
    db.metadata,
    sa.Column("tag_id", sa.Integer, sa.ForeignKey("tag.id"), nullable=False),
    sa.Column("topic_id", sa.Integer, sa.ForeignKey("topic.id"), nullable=False),
)
