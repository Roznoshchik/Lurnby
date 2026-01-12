"""migrate highlights_topics to tags_highlights

Revision ID: f5a2ecbdce8d
Revises: 9d7b79cab2cc
Create Date: 2026-01-12 12:05:00.000000

"""

from alembic import op
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = "f5a2ecbdce8d"
down_revision = "9d7b79cab2cc"
branch_labels = None
depends_on = None


def upgrade():
    """
    For each highlights_topics entry, create a tags_highlights entry
    using the corresponding Tag (matched by topic name + user_id).
    Skips duplicates.
    """
    conn = op.get_bind()

    # Get all highlights_topics entries with topic and highlight info
    entries = conn.execute(
        text(
            """
        SELECT ht.highlight_id, t.title, t.user_id
        FROM highlights_topics ht
        JOIN topic t ON t.id = ht.topic_id
        JOIN highlight h ON h.id = ht.highlight_id
    """
        )
    ).fetchall()

    for entry in entries:
        highlight_id, topic_title, user_id = entry
        if not topic_title:
            continue

        normalized_name = topic_title.strip().lower()

        # Find the corresponding tag
        tag = conn.execute(
            text(
                """
            SELECT id FROM tag
            WHERE user_id = :user_id
            AND lower(trim(name)) = :normalized_name
        """
            ),
            {"user_id": user_id, "normalized_name": normalized_name},
        ).fetchone()

        if not tag:
            continue

        tag_id = tag[0]

        # Check if entry already exists
        existing = conn.execute(
            text(
                """
            SELECT 1 FROM tags_highlights
            WHERE tag_id = :tag_id AND highlight_id = :highlight_id
        """
            ),
            {"tag_id": tag_id, "highlight_id": highlight_id},
        ).fetchone()

        if not existing:
            conn.execute(
                text(
                    """
                INSERT INTO tags_highlights (tag_id, highlight_id)
                VALUES (:tag_id, :highlight_id)
            """
                ),
                {"tag_id": tag_id, "highlight_id": highlight_id},
            )


def downgrade():
    # Data migration - no automatic downgrade
    # tags_highlights entries created by this migration will remain
    pass
