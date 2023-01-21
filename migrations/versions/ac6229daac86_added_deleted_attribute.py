"""added deleted attribute

Revision ID: ac6229daac86
Revises: ae7646aac3f6
Create Date: 2021-11-17 16:36:26.437756

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "ac6229daac86"
down_revision = "ae7646aac3f6"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###

    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.add_column(sa.Column("deleted", sa.Boolean(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.drop_column("deleted")

    # ### end Alembic commands ###
