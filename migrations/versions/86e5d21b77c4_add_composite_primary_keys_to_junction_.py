"""Add composite primary keys to junction tables

Revision ID: 86e5d21b77c4
Revises: 67a57dc2acad
Create Date: 2026-01-04 17:21:29.559592

"""

from alembic import op
import sqlalchemy as sa


revision = "86e5d21b77c4"
down_revision = "67a57dc2acad"
branch_labels = None
depends_on = None


def dedupe_junction_table(table_name, col1, col2):
    """Remove duplicate rows from a junction table using a temp table approach."""
    conn = op.get_bind()

    conn.execute(
        sa.text(
            f"""
        CREATE TEMPORARY TABLE {table_name}_deduped AS
        SELECT DISTINCT {col1}, {col2} FROM {table_name}
    """
        )
    )

    conn.execute(sa.text(f"DELETE FROM {table_name}"))

    conn.execute(
        sa.text(
            f"""
        INSERT INTO {table_name} ({col1}, {col2})
        SELECT {col1}, {col2} FROM {table_name}_deduped
    """
        )
    )

    conn.execute(sa.text(f"DROP TABLE {table_name}_deduped"))


def upgrade():
    dedupe_junction_table("tags_articles", "tag_id", "article_id")
    dedupe_junction_table("tags_highlights", "tag_id", "highlight_id")
    dedupe_junction_table("highlights_topics", "topic_id", "highlight_id")

    with op.batch_alter_table("tags_articles", schema=None) as batch_op:
        batch_op.create_primary_key("pk_tags_articles", ["tag_id", "article_id"])

    with op.batch_alter_table("tags_highlights", schema=None) as batch_op:
        batch_op.create_primary_key("pk_tags_highlights", ["tag_id", "highlight_id"])

    with op.batch_alter_table("highlights_topics", schema=None) as batch_op:
        batch_op.create_primary_key("pk_highlights_topics", ["topic_id", "highlight_id"])


def downgrade():
    with op.batch_alter_table("tags_articles", schema=None) as batch_op:
        batch_op.drop_constraint("pk_tags_articles", type_="primary")

    with op.batch_alter_table("tags_highlights", schema=None) as batch_op:
        batch_op.drop_constraint("pk_tags_highlights", type_="primary")

    with op.batch_alter_table("highlights_topics", schema=None) as batch_op:
        batch_op.drop_constraint("pk_highlights_topics", type_="primary")
