"""Add chunk positioning columns to highlight

Revision ID: 9f51a676d529
Revises: f619f0e9ac11
Create Date: 2026-02-01 14:16:49.186670

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "9f51a676d529"
down_revision = "f619f0e9ac11"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("highlight", schema=None) as batch_op:
        batch_op.add_column(sa.Column("start_chunk", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("end_chunk", sa.Integer(), nullable=True))


def downgrade():
    with op.batch_alter_table("highlight", schema=None) as batch_op:
        batch_op.drop_column("end_chunk")
        batch_op.drop_column("start_chunk")
