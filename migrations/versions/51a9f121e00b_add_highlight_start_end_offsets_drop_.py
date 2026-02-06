"""add highlight start end offsets drop position

Revision ID: 51a9f121e00b
Revises: 2b58a74fd255
Create Date: 2026-01-25 00:07:51.855494

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers, used by Alembic.
revision = "51a9f121e00b"
down_revision = "2b58a74fd255"
branch_labels = None
depends_on = None


def upgrade():
    # Backfill null UUIDs before adding NOT NULL constraint
    conn = op.get_bind()
    result = conn.execute(sa.text("SELECT id FROM highlight WHERE uuid IS NULL"))
    for row in result:
        conn.execute(
            sa.text("UPDATE highlight SET uuid = :uuid WHERE id = :id"), {"uuid": uuid.uuid4().hex, "id": row[0]}
        )

    with op.batch_alter_table("highlight", schema=None) as batch_op:
        batch_op.add_column(sa.Column("start", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("end", sa.Integer(), nullable=True))
        batch_op.alter_column("uuid", existing_type=sa.VARCHAR(), nullable=False)
        batch_op.alter_column("user_id", existing_type=sa.INTEGER(), nullable=False)
        batch_op.alter_column("archived", existing_type=sa.BOOLEAN(), nullable=False)
        batch_op.alter_column("no_topics", existing_type=sa.BOOLEAN(), nullable=False)
        batch_op.alter_column("created_date", existing_type=postgresql.TIMESTAMP(), nullable=False)
        batch_op.alter_column("review_date", existing_type=postgresql.TIMESTAMP(), nullable=False)
        batch_op.alter_column("review_schedule", existing_type=sa.INTEGER(), nullable=False)
        batch_op.alter_column("do_not_review", existing_type=sa.BOOLEAN(), nullable=False)
        batch_op.drop_column("position")


def downgrade():
    with op.batch_alter_table("highlight", schema=None) as batch_op:
        batch_op.add_column(sa.Column("position", sa.VARCHAR(), autoincrement=False, nullable=True))
        batch_op.alter_column("do_not_review", existing_type=sa.BOOLEAN(), nullable=True)
        batch_op.alter_column("review_schedule", existing_type=sa.INTEGER(), nullable=True)
        batch_op.alter_column("review_date", existing_type=postgresql.TIMESTAMP(), nullable=True)
        batch_op.alter_column("created_date", existing_type=postgresql.TIMESTAMP(), nullable=True)
        batch_op.alter_column("no_topics", existing_type=sa.BOOLEAN(), nullable=True)
        batch_op.alter_column("archived", existing_type=sa.BOOLEAN(), nullable=True)
        batch_op.alter_column("user_id", existing_type=sa.INTEGER(), nullable=True)
        batch_op.alter_column("uuid", existing_type=sa.VARCHAR(), nullable=True)
        batch_op.drop_column("end")
        batch_op.drop_column("start")
