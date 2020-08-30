"""reset the migrations

Revision ID: c10add650dd1
Revises: a2b1f1fcd256
Create Date: 2020-06-25 13:14:22.890109

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c10add650dd1'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('article', schema=None) as batch_op:
        batch_op.add_column(sa.Column('highlightedText', sa.String(), nullable=True))
        batch_op.drop_column('highlightedTextJSON')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('article', schema=None) as batch_op:
        batch_op.add_column(sa.Column('highlightedTextJSON', sa.VARCHAR(), nullable=True))
        batch_op.drop_column('highlightedText')

    # ### end Alembic commands ###
