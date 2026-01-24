"""Convert bookmarks to array format

Revision ID: 4ec7d74236b2
Revises: 2b58a74fd255
Create Date: 2026-01-23 13:29:33.766481

Converts bookmarks from object format {name: percentage} to array format:
[{name, offset, legacy}] where legacy holds the old percentage value.
"""

from alembic import op
import sqlalchemy as sa
import json


# revision identifiers, used by Alembic.
revision = "4ec7d74236b2"
down_revision = "2b58a74fd255"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    results = conn.execute(sa.text("SELECT id, bookmarks FROM article WHERE bookmarks IS NOT NULL"))

    for row in results:
        article_id, bookmarks_str = row
        if not bookmarks_str:
            continue

        try:
            old_bookmarks = json.loads(bookmarks_str)
        except json.JSONDecodeError:
            continue

        # Skip if already in array format
        if isinstance(old_bookmarks, list):
            continue

        # Convert {name: value} to [{name, start, legacy}]
        new_bookmarks = []
        for name, value in old_bookmarks.items():
            new_bookmarks.append({"name": name, "start": None, "legacy": value})

        conn.execute(
            sa.text("UPDATE article SET bookmarks = :bookmarks WHERE id = :id"),
            {"bookmarks": json.dumps(new_bookmarks), "id": article_id},
        )


def downgrade():
    conn = op.get_bind()
    results = conn.execute(sa.text("SELECT id, bookmarks FROM article WHERE bookmarks IS NOT NULL"))

    for row in results:
        article_id, bookmarks_str = row
        if not bookmarks_str:
            continue

        try:
            bookmarks_array = json.loads(bookmarks_str)
        except json.JSONDecodeError:
            continue

        # Skip if already in object format
        if isinstance(bookmarks_array, dict):
            continue

        # Convert [{name, start, legacy}] back to {name: value}
        # Handle both 'start' (new) and 'offset' (old) field names
        old_bookmarks = {}
        for bookmark in bookmarks_array:
            name = bookmark.get("name")
            value = bookmark.get("start") or bookmark.get("offset") or bookmark.get("legacy")
            if name and value is not None:
                old_bookmarks[name] = value

        conn.execute(
            sa.text("UPDATE article SET bookmarks = :bookmarks WHERE id = :id"),
            {"bookmarks": json.dumps(old_bookmarks), "id": article_id},
        )
