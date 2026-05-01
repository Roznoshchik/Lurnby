from datetime import datetime, timezone

import sqlalchemy as sa
import sqlalchemy.orm as so

from app.models.base import db, generate_str_id

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models import Article


class ArticleChunk(db.Model):
    __tablename__ = "article_chunk"
    __table_args__ = (sa.UniqueConstraint("article_id", "idx", name="uq_article_chunk_article_idx"),)

    uuid: so.Mapped[str] = so.mapped_column(sa.String, primary_key=True, default=generate_str_id)
    article_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey("article.id"), index=True)
    idx: so.Mapped[int] = so.mapped_column(sa.Integer)
    start_offset: so.Mapped[int] = so.mapped_column(sa.Integer)
    text_length: so.Mapped[int] = so.mapped_column(sa.Integer)
    content_tree: so.Mapped[dict | None] = so.mapped_column(sa.JSON)
    created_at: so.Mapped[datetime] = so.mapped_column(sa.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: so.Mapped[datetime] = so.mapped_column(
        sa.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    article: so.Mapped["Article"] = so.relationship(back_populates="chunks")  # noqa: F821

    def to_dict(self, include_tree=True):
        return {
            "uuid": self.uuid,
            "idx": self.idx,
            "start_offset": self.start_offset,
            "text_length": self.text_length,
            "content_tree": self.content_tree if include_tree else None,
        }
