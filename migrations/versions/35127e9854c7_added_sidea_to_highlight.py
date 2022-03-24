"""added Prompt to highlight

Revision ID: 35127e9854c7
Revises: 0c05d3df71bd
Create Date: 2022-03-21 22:38:50.932324

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '35127e9854c7'
down_revision = '0c05d3df71bd'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    
    with op.batch_alter_table('highlight', schema=None) as batch_op:
        batch_op.add_column(sa.Column('Prompt', sa.String(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('highlight', schema=None) as batch_op:
        batch_op.drop_column('Prompt')

    # ### end Alembic commands ###
