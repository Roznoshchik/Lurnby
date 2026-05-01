import copy
from datetime import datetime, date, timezone
import json
import math
import re
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from bs4 import BeautifulSoup, NavigableString, Tag
from flask import url_for
from flask_login import current_user
import sqlalchemy as sa
import sqlalchemy.orm as so
from sqlalchemy import desc, func, Index, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from app.models.base import db
from app.models.article_chunk import ArticleChunk
from app.models.associations import tags_articles

if TYPE_CHECKING:
    from app.models.highlight import Highlight


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
            print("[BookmarkMigration] Skipping - no chunks")
            return

        # If no bookmarks but progress exists, create furthest from progress
        if not self.bookmarks and self.progress > 0:
            print(f"[BookmarkMigration] No bookmarks but progress={self.progress}%, creating furthest from progress")
            bookmarks = {"furthest": self.progress}
        else:
            bookmarks = self.bookmarks

        if not bookmarks:
            print("[BookmarkMigration] No bookmarks and no progress, skipping")
            return

        # Handle string format from old String column (parse if needed)
        if isinstance(bookmarks, str):
            try:
                bookmarks = json.loads(bookmarks)
            except json.JSONDecodeError:
                print(f"[BookmarkMigration] Failed to parse JSON: {bookmarks}")
                return

        # Already migrated if it's a list
        if isinstance(bookmarks, list):
            print(f"[BookmarkMigration] Already migrated (list format): {bookmarks}")
            return

        # Legacy format was a dict {name: percentage}
        if not isinstance(bookmarks, dict):
            print(f"[BookmarkMigration] Unknown format: {type(bookmarks)}")
            return

        print(f"[BookmarkMigration] Migrating legacy bookmarks: {bookmarks}")
        print(f"[BookmarkMigration] Total length: {self.total_length}, Chunk count: {len(self.chunks)}")

        migrated = []
        for name, percentage in bookmarks.items():
            # Clamp percentage to 100% max
            clamped_percentage = min(percentage, 100.0)
            global_offset = int((clamped_percentage / 100) * self.total_length)

            if percentage != clamped_percentage:
                print(
                    f"[BookmarkMigration] {name}: {percentage}%"
                    f" (clamped to {clamped_percentage}%) → global_offset: {global_offset}"
                )
            else:
                print(f"[BookmarkMigration] {name}: {percentage}% → global_offset: {global_offset}")

            # Handle edge case: offset at or past end of article
            if global_offset >= self.total_length:
                last_chunk = self.chunks[-1]
                local_offset = last_chunk.text_length - 1  # Last character of last chunk
                print(
                    f"[BookmarkMigration]   At end of article, using last chunk {last_chunk.idx}, offset: {local_offset}"
                )
                migrated.append(
                    {
                        "name": name,
                        "chunk": last_chunk.idx,
                        "offset": local_offset,
                    }
                )
                continue

            for chunk in self.chunks:
                if chunk.start_offset <= global_offset < chunk.start_offset + chunk.text_length:
                    local_offset = global_offset - chunk.start_offset
                    print(
                        f"[BookmarkMigration]   Found in chunk {chunk.idx}"
                        f" (start: {chunk.start_offset}, length: {chunk.text_length}),"
                        f" local_offset: {local_offset}"
                    )
                    migrated.append(
                        {
                            "name": name,
                            "chunk": chunk.idx,
                            "offset": local_offset,
                        }
                    )
                    break

        print(f"[BookmarkMigration] Migration complete: {migrated}")
        self.bookmarks = migrated

    def reanchor_highlights(self):
        """Re-anchor highlights by searching for their text in chunks.

        Searches within single chunks first, then adjacent chunk pairs.
        Sets chunk-based positions (start_chunk, start, end_chunk, end).
        """
        import re

        if not self.chunks:
            return

        chunks = sorted(self.chunks, key=lambda c: c.idx)
        # Normalize \n to space; keep \x00 (void element placeholder) for offset accuracy
        chunk_texts = [(c.idx, self._get_chunk_flat_text(c.content_tree).replace("\n", " ")) for c in chunks]

        for highlight in self.highlights:
            if highlight.archived or not highlight.text:
                continue

            highlight_tree = self.build_content_tree(content=highlight.text)
            search_text = self._get_chunk_flat_text(highlight_tree).replace("\n", " ").rstrip(" ")

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

    def _get_chunk_flat_text(self, content_tree):
        """Extract plain text from a chunk's content tree."""
        if not content_tree:
            return ""

        def extract(node):
            if node["type"] == "text":
                return node["text"]
            if node["type"] in ("void", "anchor"):
                return "\x00"
            if node["type"] == "element":
                return "".join(extract(child) for child in node.get("children", []))
            return ""

        return "".join(extract(node) for node in content_tree)

    def build_content_tree(self, content=None):
        """Build a content tree with text offsets from HTML content.

        Args:
            content: HTML string to parse. Defaults to self.content.

        Returns:
            List of tree nodes with text offsets.
        """
        VOID_ELEMENTS = {"br", "hr"}
        ANCHOR_ELEMENTS = {"img"}
        BLOCK_CONTENT = {"p", "li", "h1", "h2", "h3", "h4", "h5", "h6", "blockquote", "pre", "figcaption"}

        source = content if content is not None else self.content
        soup = BeautifulSoup(source or "", "lxml")
        offset = 0
        # Track boundary state for smart spacing
        last_char = [None]  # Last character emitted (use list for nonlocal mutation)
        pending_space = [False]  # Whether whitespace was stripped that might need reinserting

        def is_legacy_highlight_span(node):
            if node.name != "span":
                return False
            node_id = node.get("id", "")
            if node_id.startswith("highlight"):
                return True
            node_class = node.get("class", [])
            if isinstance(node_class, str):
                node_class = [node_class]
            return any("highlight" in c for c in node_class)

        def process(node):
            nonlocal offset

            if isinstance(node, NavigableString):
                raw = str(node)
                had_leading_ws = raw and raw[0] in " \t\n\r\xa0"
                had_trailing_ws = raw and raw[-1] in " \t\n\r\xa0"
                # Normalize typographic characters
                raw = raw.replace("\u2019", "'").replace("\u2018", "'")  # curly single quotes
                raw = raw.replace("\u201c", '"').replace("\u201d", '"')  # curly double quotes
                raw = raw.replace("\u2013", "-").replace("\u2014", "-")  # en-dash, em-dash
                text = re.sub(r"[\xa0\s]+", " ", raw).strip()
                if not text:
                    if had_leading_ws or had_trailing_ws:
                        pending_space[0] = True
                    return None
                # Insert space if whitespace was present between content
                # But don't insert space before closing punctuation or after opening punctuation
                first_char = text[0] if text else ""
                before_closing = first_char not in ",.;:!?)\"']"
                after_opening = last_char[0] not in "\"'([" if last_char[0] else True
                needs_space = (
                    (pending_space[0] or had_leading_ws) and last_char[0] and before_closing and after_opening
                )
                if needs_space:
                    text = " " + text
                pending_space[0] = had_trailing_ws
                last_char[0] = text[-1] if text else None
                start = offset
                offset += len(text)
                return {"type": "text", "text": text, "start": start, "length": len(text)}

            if isinstance(node, Tag):
                # Legacy highlight span - unwrap (keep children, discard span)
                if is_legacy_highlight_span(node):
                    children = []
                    for child in node.children:
                        child_node = process(child)
                        if child_node:
                            if isinstance(child_node, list):
                                children.extend(child_node)
                            else:
                                children.append(child_node)
                    if children:
                        return children if len(children) > 1 else children[0]
                    return None

                if node.name in VOID_ELEMENTS:
                    start = offset
                    offset += 1
                    return {"type": "void", "tag": node.name, "start": start, "length": 1}

                if node.name in ANCHOR_ELEMENTS:
                    start = offset
                    offset += 1
                    return {
                        "type": "anchor",
                        "tag": node.name,
                        "src": node.get("src"),
                        "alt": node.get("alt"),
                        "start": start,
                        "length": 1,
                    }

                # Reset spacing state at block boundaries
                if node.name in BLOCK_CONTENT:
                    pending_space[0] = False
                    last_char[0] = None

                children = []
                for child in node.children:
                    child_node = process(child)
                    if child_node:
                        if isinstance(child_node, list):
                            children.extend(child_node)
                        else:
                            children.append(child_node)

                if not children:
                    return None

                if node.name in BLOCK_CONTENT:
                    children.append({"type": "text", "text": "\n", "start": offset, "length": 1})
                    offset += 1

                first = children[0]
                last = children[-1]
                end = last["end"] if "end" in last else last["start"] + last["length"]

                return {"type": "element", "tag": node.name, "children": children, "start": first["start"], "end": end}

            return None

        tree = []
        root = soup.body or soup
        for child in root.children:
            node = process(child)
            if node:
                if isinstance(node, list):
                    tree.extend(node)
                else:
                    tree.append(node)

        return tree

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

        full_tree = self.build_content_tree()
        if not full_tree:
            self.chunk_count = 0
            self.total_length = 0
            return

        total_length = self._get_tree_end_offset(full_tree)

        if total_length <= min_size:
            self._create_chunk_from_tree(full_tree, idx=0, start_offset=0)
            self.chunk_count = 1
            self.total_length = total_length
            self.reanchor_highlights()
            return

        split_offsets = self._find_split_points(full_tree, total_length, min_size, max_size)
        chunks_trees = self._slice_tree_at_offsets(full_tree, split_offsets)

        global_offset = 0
        for idx, chunk_tree in enumerate(chunks_trees):
            rebased_tree = self._rebase_tree_offsets(chunk_tree)
            chunk_length = self._get_tree_end_offset(rebased_tree)
            self._create_chunk_from_tree(rebased_tree, idx=idx, start_offset=global_offset)
            global_offset += chunk_length

        self.chunk_count = len(chunks_trees)
        self.total_length = total_length
        self.reanchor_highlights()

    def _get_tree_end_offset(self, tree):
        """Get the end offset of a tree (offset after last character)."""
        if not tree:
            return 0
        last = tree[-1]
        return last.get("end") or (last.get("start", 0) + last.get("length", 0))

    def _find_split_points(self, tree, total_length, min_size, max_size):
        """Find optimal split points in the tree."""
        split_points = []
        current_start = 0

        while current_start + min_size < total_length:
            search_start = current_start + min_size
            search_end = min(current_start + max_size, total_length)

            best = self._find_best_split_in_range(tree, search_start, search_end)
            if best is None:
                best = search_end

            split_points.append(best)
            current_start = best

        return split_points

    def _find_best_split_in_range(self, tree, start, end):
        """Find the best split point between start and end offsets."""
        candidates = []

        def walk(node, depth):
            node_start = node.get("start", 0)
            node_end = node.get("end") or (node_start + node.get("length", 0))

            if node_end <= start or node_start >= end:
                return

            if node["type"] == "text":
                text = node["text"]
                text_start = node["start"]

                for i, char in enumerate(text):
                    offset = text_start + i
                    if offset < start or offset >= end:
                        continue

                    if char in ".!?" and i + 1 < len(text) and text[i + 1] == " ":
                        candidates.append((offset + 2, 2, depth))
                    elif char == " ":
                        candidates.append((offset + 1, 1, depth))

            elif node["type"] == "element":
                tag = node["tag"]

                if tag in {"h1", "h2", "h3"} and node_start >= start and node_start < end:
                    candidates.append((node_start, 4, depth))
                elif tag in {"p", "div", "blockquote", "li", "pre", "figcaption"}:
                    if node_end >= start and node_end < end:
                        candidates.append((node_end, 3, depth))

                for child in node.get("children", []):
                    walk(child, depth + 1)

        for node in tree:
            walk(node, 0)

        if not candidates:
            return None

        candidates.sort(key=lambda x: (-x[1], x[2]))
        return candidates[0][0]

    def _slice_tree_at_offsets(self, tree, split_offsets):
        """Slice tree at given offsets, adding continues/continuation flags."""
        if not split_offsets:
            return [tree]

        chunks = []
        remaining = copy.deepcopy(tree)

        for split_offset in split_offsets:
            left, right = self._split_tree_at_offset(remaining, split_offset)
            chunks.append(left)
            remaining = right

        chunks.append(remaining)
        return chunks

    def _split_tree_at_offset(self, tree, offset):
        """Split tree at offset, returning (left, right) trees."""
        left = []
        right = []

        for node in tree:
            node_start = node.get("start", 0)
            node_end = node.get("end") or (node_start + node.get("length", 0))

            if node_end <= offset:
                left.append(copy.deepcopy(node))
            elif node_start >= offset:
                right.append(copy.deepcopy(node))
            else:
                left_part, right_part = self._split_node_at_offset(node, offset)
                if left_part:
                    left.append(left_part)
                if right_part:
                    right.append(right_part)

        return left, right

    def _split_node_at_offset(self, node, offset):
        """Split a single node at offset, adding continues/continuation flags."""
        node_start = node.get("start", 0)

        if node["type"] == "text":
            text = node["text"]
            split_idx = offset - node_start
            left_text = text[:split_idx]
            right_text = text[split_idx:]

            left_node = None
            right_node = None

            if left_text:
                left_node = {
                    "type": "text",
                    "text": left_text,
                    "start": node_start,
                    "length": len(left_text),
                }
            if right_text:
                right_node = {
                    "type": "text",
                    "text": right_text,
                    "start": offset,
                    "length": len(right_text),
                }

            return left_node, right_node

        elif node["type"] == "element":
            children = node.get("children", [])
            left_children = []
            right_children = []

            for child in children:
                child_start = child.get("start", 0)
                child_end = child.get("end") or (child_start + child.get("length", 0))

                if child_end <= offset:
                    left_children.append(copy.deepcopy(child))
                elif child_start >= offset:
                    right_children.append(copy.deepcopy(child))
                else:
                    left_part, right_part = self._split_node_at_offset(child, offset)
                    if left_part:
                        left_children.append(left_part)
                    if right_part:
                        right_children.append(right_part)

            left_node = None
            right_node = None

            if left_children:
                first = left_children[0]
                last = left_children[-1]
                left_end = last.get("end") or (last.get("start", 0) + last.get("length", 0))
                left_node = {
                    "type": "element",
                    "tag": node["tag"],
                    "children": left_children,
                    "start": first.get("start", node_start),
                    "end": left_end,
                    "continues": True,
                }
                # Preserve continuation flag from original node
                if node.get("continuation"):
                    left_node["continuation"] = True

            if right_children:
                first = right_children[0]
                last = right_children[-1]
                right_end = last.get("end") or (last.get("start", 0) + last.get("length", 0))
                right_node = {
                    "type": "element",
                    "tag": node["tag"],
                    "children": right_children,
                    "start": first.get("start", offset),
                    "end": right_end,
                    "continuation": True,
                }
                # Preserve continues flag from original node
                if node.get("continues"):
                    right_node["continues"] = True

            return left_node, right_node

        else:
            if node_start < offset:
                return copy.deepcopy(node), None
            else:
                return None, copy.deepcopy(node)

    def _rebase_tree_offsets(self, tree):
        """Rebase tree offsets to start at 0."""
        if not tree:
            return tree

        base_offset = tree[0].get("start", 0)
        if base_offset == 0:
            return tree

        def rebase(node):
            if "start" in node:
                node["start"] -= base_offset
            if "end" in node:
                node["end"] -= base_offset
            for child in node.get("children", []):
                rebase(child)

        rebased = copy.deepcopy(tree)
        for node in rebased:
            rebase(node)

        return rebased

    def _create_chunk_from_tree(self, tree, idx, start_offset):
        """Create an ArticleChunk from a tree."""
        text_length = self._get_tree_end_offset(tree)
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
