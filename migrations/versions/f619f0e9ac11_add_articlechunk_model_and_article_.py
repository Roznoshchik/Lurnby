"""Add ArticleChunk model and article chunk metadata

Revision ID: f619f0e9ac11
Revises: 51a9f121e00b
Create Date: 2026-01-31 14:44:07.049887

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "f619f0e9ac11"
down_revision = "51a9f121e00b"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "article_chunk",
        sa.Column("uuid", sa.String(), nullable=False),
        sa.Column("article_id", sa.Integer(), nullable=False),
        sa.Column("idx", sa.Integer(), nullable=False),
        sa.Column("start_offset", sa.Integer(), nullable=False),
        sa.Column("text_length", sa.Integer(), nullable=False),
        sa.Column("content_tree", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["article_id"], ["article.id"], name=op.f("fk_article_chunk_article_id_article")),
        sa.PrimaryKeyConstraint("uuid", name=op.f("pk_article_chunk")),
        sa.UniqueConstraint("article_id", "idx", name="uq_article_chunk_article_idx"),
    )
    with op.batch_alter_table("article_chunk", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_article_chunk_article_id"), ["article_id"], unique=False)

    with op.batch_alter_table("article", schema=None) as batch_op:
        batch_op.add_column(sa.Column("chunk_count", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("total_length", sa.Integer(), nullable=True))


def downgrade():
    with op.batch_alter_table("article", schema=None) as batch_op:
        batch_op.drop_column("total_length")
        batch_op.drop_column("chunk_count")

    with op.batch_alter_table("article_chunk", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_article_chunk_article_id"))

    op.drop_table("article_chunk")
