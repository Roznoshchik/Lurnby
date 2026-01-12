"""backfill tags from topics

Revision ID: 9d7b79cab2cc
Revises: ce7c5abaa88d
Create Date: 2026-01-12 12:00:00.000000

"""

from alembic import op
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = "9d7b79cab2cc"
down_revision = "ce7c5abaa88d"
branch_labels = None
depends_on = None


def upgrade():
    """
    For each Topic, create a Tag if one doesn't exist with matching normalized name.
    Uses lower(trim(name)) for matching.
    """
    conn = op.get_bind()

    # Get all topics
    topics = conn.execute(
        text(
            """
        SELECT id, title, user_id, archived, last_used
        FROM topic
    """
        )
    ).fetchall()

    for topic in topics:
        topic_id, title, user_id, archived, last_used = topic
        if not title:
            continue

        normalized_name = title.strip().lower()

        # Check if tag already exists
        existing = conn.execute(
            text(
                """
            SELECT id FROM tag
            WHERE user_id = :user_id
            AND lower(trim(name)) = :normalized_name
        """
            ),
            {"user_id": user_id, "normalized_name": normalized_name},
        ).fetchone()

        if existing:
            # Update last_used if topic's is more recent
            conn.execute(
                text(
                    """
                UPDATE tag
                SET last_used = GREATEST(COALESCE(last_used, :last_used), COALESCE(:last_used, last_used))
                WHERE id = :tag_id
            """
                ),
                {"tag_id": existing[0], "last_used": last_used},
            )
        else:
            # Create new tag
            conn.execute(
                text(
                    """
                INSERT INTO tag (name, user_id, archived, last_used)
                VALUES (:name, :user_id, :archived, :last_used)
            """
                ),
                {
                    "name": title.strip(),
                    "user_id": user_id,
                    "archived": archived or False,
                    "last_used": last_used,
                },
            )


def downgrade():
    # Data migration - no automatic downgrade
    # Tags created by this migration will remain
    pass
