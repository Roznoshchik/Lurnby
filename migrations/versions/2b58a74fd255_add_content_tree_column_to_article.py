"""Add content_tree column to Article

Revision ID: 2b58a74fd255
Revises: f5a2ecbdce8d
Create Date: 2026-01-22 13:44:14.569463

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "2b58a74fd255"
down_revision = "f5a2ecbdce8d"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("article", schema=None) as batch_op:
        batch_op.add_column(sa.Column("content_tree", sa.JSON(), nullable=True))


def downgrade():
    with op.batch_alter_table("article", schema=None) as batch_op:
        batch_op.drop_column("content_tree")
