"""remove untagged column from highlight

Revision ID: a25b93359b97
Revises: 86e5d21b77c4
Create Date: 2026-01-11 23:42:15.364048

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "a25b93359b97"
down_revision = "86e5d21b77c4"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("highlight", schema=None) as batch_op:
        batch_op.drop_column("untagged")


def downgrade():
    with op.batch_alter_table("highlight", schema=None) as batch_op:
        batch_op.add_column(sa.Column("untagged", sa.BOOLEAN(), autoincrement=False, nullable=True))
