from datetime import datetime, date, timezone
import json
import math
import re
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from bs4 import BeautifulSoup
from flask import url_for
from flask_login import current_user
import sqlalchemy as sa
import sqlalchemy.orm as so
from sqlalchemy import desc, func, Index, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID


from app.helpers.content_tree import (
    build_content_tree,
    get_flat_text,
    get_tree_end_offset,
    find_split_points,
    slice_tree_at_offsets,
    rebase_tree_offsets,
)
from app.models.base import db
from app.models.article_chunk import ArticleChunk
from app.models.associations import tags_articles

if TYPE_CHECKING:
    from app.models.highlight import Highlight
    from app.models.tag import Tag


class Article(db.Model):
    __mapper_args__ = {"confirm_deleted_rows": False}

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    uuid: so.Mapped[UUID] = so.mapped_column("uuid", PG_UUID(as_uuid=True), default=uuid4, index=True, unique=True)
    unread: so.Mapped[bool] = so.mapped_column(sa.Boolean, index=True, default=True)
    title: so.Mapped[str] = so.mapped_column(sa.String(255), default="Something went wrong", index=True)
    filetype: so.Mapped[str | None] = so.mapped_column(sa.String(32))
    source: so.Mapped[str | None] = so.mapped_column(sa.String(500))
    source_url: so.Mapped[str | None] = so.mapped_column(sa.String(500))
    content: so.Mapped[str | None] = so.mapped_column(sa.Text)
    date_read: so.Mapped[datetime | None] = so.mapped_column(sa.DateTime)
    date_read_date: so.Mapped[date | None] = so.mapped_column(sa.Date)  # legacy: use date_read instead
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey("user.id"), index=True)
    highlights: so.Mapped[list["Highlight"]] = so.relationship(backref="article")
    archived: so.Mapped[bool] = so.mapped_column(sa.Boolean, index=True, default=False)
    highlightedText: so.Mapped[str | None] = so.mapped_column(sa.String, default="")
    tags: so.Mapped[list["Tag"]] = so.relationship(secondary=tags_articles, back_populates="articles")
    progress: so.Mapped[float] = so.mapped_column(sa.Float, index=True, default=0.0)
    bookmarks: so.Mapped[list[dict] | None] = so.mapped_column(JSONB, default=[])
    done: so.Mapped[bool] = so.mapped_column(sa.Boolean, default=False)
    notes: so.Mapped[str] = so.mapped_column(sa.Text, default="")
    reflections: so.Mapped[str] = so.mapped_column(sa.Text, default="")

    article_created_date: so.Mapped[datetime | None] = so.mapped_column(
        sa.DateTime, default=lambda: datetime.now(timezone.utc)
    )
    read_time: so.Mapped[str | None] = so.mapped_column(sa.String)
    processing: so.Mapped[bool] = so.mapped_column(sa.Boolean, default=False)
    chunk_count: so.Mapped[int | None] = so.mapped_column(sa.Integer)
    total_length: so.Mapped[int | None] = so.mapped_column(sa.Integer)
    chunks: so.Mapped[list["ArticleChunk"]] = so.relationship(
        back_populates="article",
        order_by="ArticleChunk.idx",
        cascade="all, delete-orphan",
    )

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
        return [tag.name for tag in self.tags]

    @property
    def tag_ids(self):
        """Get tag IDs efficiently from junction table without loading Tag objects."""
        return db.session.scalars(select(tags_articles.c.tag_id).where(tags_articles.c.article_id == self.id)).all()

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

    def to_dict(self, preview=True, with_content=False):
        # Handle None and NaN progress values
        progress = self.progress
        if progress is None:
            progress = 0.0
        elif math.isnan(progress):
            progress = 0.0

        has_chunks = self.chunk_count and self.chunk_count > 0

        data = {
            "id": self.id,
            "uuid": self.uuid,
            "user_id": self.user_id,
            "source": self.source or self.source_url,
            "source_url": self.source_url,
            "title": self.title,
            "filetype": self.filetype,
            "content": self.content if with_content else None,
            "unread": self.unread,
            "archived": self.archived,
            "done": self.done,
            "date_read": self.date_read,
            "notes": self.notes if not preview else None,
            "reflections": self.reflections if not preview else None,
            "read_time": self.read_time,
            "progress": progress,
            "bookmarks": self.bookmarks or [],
            "created_at": self.article_created_date,
            "highlights_count": len(self.highlights),
            "tags": [tag.to_dict() for tag in self.tags],
            "chunk_count": self.chunk_count,
            "total_length": self.total_length,
            "chunks_meta": [{"idx": c.idx, "text_length": c.text_length} for c in self.chunks] if has_chunks else None,
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

    def _ensure_chunks_built(self):
        """Build chunks on-demand if missing, migrate bookmarks and highlights."""
        if self.content and not self.chunks:
            self.build_chunks()
            self._migrate_legacy_bookmarks()
            self.reanchor_highlights()
            db.session.commit()

    def _migrate_legacy_bookmarks(self):
        """Convert legacy bookmarks {name: percentage} to [{name, chunk, offset}]."""
        if not self.chunks:
            return

        # If no bookmarks but progress exists, create furthest from progress
        if not self.bookmarks and self.progress > 0:
            bookmarks = {"furthest": self.progress}
        else:
            bookmarks = self.bookmarks

        if not bookmarks:
            return

        # Handle string format from old String column (parse if needed)
        if isinstance(bookmarks, str):
            try:
                bookmarks = json.loads(bookmarks)
            except json.JSONDecodeError:
                return

        # Already migrated if it's a list
        if isinstance(bookmarks, list):
            return

        # Legacy format was a dict {name: percentage}
        if not isinstance(bookmarks, dict):
            return

        migrated = []
        for name, percentage in bookmarks.items():
            clamped_percentage = min(percentage, 100.0)
            global_offset = int((clamped_percentage / 100) * self.total_length)

            if global_offset >= self.total_length:
                last_chunk = self.chunks[-1]
                migrated.append(
                    {
                        "name": name,
                        "chunk": last_chunk.idx,
                        "offset": last_chunk.text_length - 1,
                    }
                )
                continue

            for chunk in self.chunks:
                if chunk.start_offset <= global_offset < chunk.start_offset + chunk.text_length:
                    migrated.append(
                        {
                            "name": name,
                            "chunk": chunk.idx,
                            "offset": global_offset - chunk.start_offset,
                        }
                    )
                    break

        self.bookmarks = migrated

    def reanchor_highlights(self):
        """Re-anchor highlights by searching for their text in chunks.

        Searches within single chunks first, then adjacent chunk pairs.
        Sets chunk-based positions (start_chunk, start, end_chunk, end).
        """
        if not self.chunks:
            return

        chunks = sorted(self.chunks, key=lambda c: c.idx)
        # Normalize \n to space; keep \x00 (void element placeholder) for offset accuracy
        chunk_texts = [(c.idx, get_flat_text(c.content_tree).replace("\n", " ")) for c in chunks]

        for highlight in self.highlights:
            if highlight.archived or not highlight.text:
                continue

            highlight_tree = build_content_tree(highlight.text)
            search_text = get_flat_text(highlight_tree).replace("\n", " ").rstrip(" ")

            if not search_text:
                continue

            # Build a flexible pattern: split on any whitespace/void sequences and
            # rejoin with [\x00\s]* so the pattern tolerates spaces added/removed
            # around inline elements (e.g. <code>) between capture and content tree
            pieces = re.split(r"[\x00\s]+", search_text.strip())
            pattern = r"[\x00\s]*".join(re.escape(p) for p in pieces if p)

            found = False

            for i, (idx, text) in enumerate(chunk_texts):
                m = re.search(pattern, text)
                if m:
                    highlight.start_chunk = idx
                    highlight.start = m.start()
                    highlight.end_chunk = idx
                    highlight.end = m.end()
                    found = True
                    break

                # Adjacent pair search
                if i + 1 < len(chunk_texts):
                    next_idx, next_text = chunk_texts[i + 1]
                    combined = text + next_text
                    m = re.search(pattern, combined)
                    if m and m.start() < len(text) < m.end():
                        highlight.start_chunk = idx
                        highlight.start = m.start()
                        highlight.end_chunk = next_idx
                        highlight.end = m.end() - len(text)
                        found = True
                        break

            if not found:
                highlight.start_chunk = None
                highlight.start = None
                highlight.end_chunk = None
                highlight.end = None

    def build_chunks(self, min_size=8000, max_size=15000):
        """Split content into chunks and build content_tree for each.

        Each chunk gets its own content_tree with LOCAL offsets starting at 0.
        Elements split across chunks get continues/continuation flags.
        """
        self.chunks.clear()

        if not self.content:
            self.chunk_count = 0
            self.total_length = 0
            return

        full_tree = build_content_tree(self.content)
        if not full_tree:
            self.chunk_count = 0
            self.total_length = 0
            return

        total_length = get_tree_end_offset(full_tree)

        if total_length <= min_size:
            self._create_chunk_from_tree(full_tree, idx=0, start_offset=0)
            self.chunk_count = 1
            self.total_length = total_length
            self.reanchor_highlights()
            return

        split_offsets = find_split_points(full_tree, total_length, min_size, max_size)
        chunks_trees = slice_tree_at_offsets(full_tree, split_offsets)

        global_offset = 0
        for idx, chunk_tree in enumerate(chunks_trees):
            rebased_tree = rebase_tree_offsets(chunk_tree)
            chunk_length = get_tree_end_offset(rebased_tree)
            self._create_chunk_from_tree(rebased_tree, idx=idx, start_offset=global_offset)
            global_offset += chunk_length

        self.chunk_count = len(chunks_trees)
        self.total_length = total_length
        self.reanchor_highlights()

    def _create_chunk_from_tree(self, tree, idx, start_offset):
        """Create an ArticleChunk from a tree."""
        text_length = get_tree_end_offset(tree)
        chunk = ArticleChunk(
            article_id=self.id,
            idx=idx,
            start_offset=start_offset,
            text_length=text_length,
            content_tree=tree,
        )
        db.session.add(chunk)
        self.chunks.append(chunk)

    def add_tag(self, tag):
        if not self.is_added_tag(tag):
            self.tags.append(tag)
            tag.article_count += 1
            if self.id and len(self.highlights) > 0:
                for h in self.highlights:
                    tag.highlight_count += 1
                    h.add_tag(tag)

    def remove_tag(self, tag):
        if self.is_added_tag(tag):
            self.tags.remove(tag)
            tag.article_count -= 1
            if self.id and len(self.highlights) > 0:
                for h in self.highlights:
                    tag.highlight_count -= 1
                    h.remove_tag(tag)

    def is_added_tag(self, tag):
        # New article can't have tags yet
        if not self.id:
            return False
        return db.session.query(
            db.exists().where(
                db.and_(
                    tags_articles.c.tag_id == tag.id,
                    tags_articles.c.article_id == self.id,
                )
            )
        ).scalar()

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

        q = db.session.query(Tag).filter(~Tag.id.in_(sub)).filter_by(user_id=user.id, archived=False).all()

        return q


articles_lower_title_key = Index("articles_lower_title_key", func.lower(Article.title))
