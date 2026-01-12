"""add last_used column to tag

Revision ID: ce7c5abaa88d
Revises: a25b93359b97
Create Date: 2026-01-12 11:38:21.166001

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "ce7c5abaa88d"
down_revision = "a25b93359b97"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("tag", sa.Column("last_used", sa.DateTime(), nullable=True))


def downgrade():
    op.drop_column("tag", "last_used")
