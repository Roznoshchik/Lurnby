"""added event class

Revision ID: 83c88503ad2b
Revises: 27e6fca13770
Create Date: 2021-10-29 15:19:04.990894

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "83c88503ad2b"
down_revision = "27e6fca13770"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "event",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("date", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"], ["user.id"], name=op.f("fk_event_user_id_user")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_event")),
    )

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ##

    op.drop_table("event")
    # ### end Alembic commands ###
