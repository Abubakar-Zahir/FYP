"""add comment labels and the comment_themes table

Revision ID: 0008
Revises: 0007
"""

import sqlalchemy as sa
from alembic import op

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("comments") as batch:
        batch.add_column(sa.Column("label", sa.String(length=20), nullable=True))
        batch.add_column(sa.Column("label_model_version", sa.String(length=200), nullable=True))
    op.create_table(
        "comment_themes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("theme", sa.Text(), nullable=False),
        sa.Column("size", sa.Integer(), nullable=False),
        sa.Column("dominant_label", sa.String(length=20), nullable=False),
        sa.Column("example_comment_ids", sa.JSON(), nullable=False),
        sa.Column("idea", sa.Text(), nullable=False),
        sa.Column("model_version", sa.String(length=200), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_comment_themes_user_id", "comment_themes", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_comment_themes_user_id", table_name="comment_themes")
    op.drop_table("comment_themes")
    with op.batch_alter_table("comments") as batch:
        batch.drop_column("label_model_version")
        batch.drop_column("label")
