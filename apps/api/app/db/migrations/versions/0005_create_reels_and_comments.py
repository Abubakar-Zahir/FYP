"""create reels and comments tables

Revision ID: 0005
Revises: 0004
"""

import sqlalchemy as sa
from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "reels",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("source", sa.String(length=20), nullable=False),
        sa.Column("ig_media_id", sa.String(length=64), nullable=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("caption", sa.Text(), nullable=True),
        sa.Column("permalink", sa.Text(), nullable=True),
        sa.Column("posted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("r2_key", sa.String(length=300), nullable=True),
        sa.Column("views", sa.Integer(), nullable=True),
        sa.Column("reach", sa.Integer(), nullable=True),
        sa.Column("saves", sa.Integer(), nullable=True),
        sa.Column("shares", sa.Integer(), nullable=True),
        sa.Column("avg_watch_time_s", sa.Float(), nullable=True),
        sa.Column("outlier_score", sa.Float(), nullable=True),
        sa.Column("metrics_fetched_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "ig_media_id", name="uq_reels_user_media"),
    )
    op.create_index("ix_reels_user_id", "reels", ["user_id"])
    op.create_table(
        "comments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("reel_id", sa.Uuid(), nullable=False),
        sa.Column("ig_comment_id", sa.String(length=64), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("posted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["reel_id"], ["reels.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "ig_comment_id", name="uq_comments_user_comment"),
    )
    op.create_index("ix_comments_user_id", "comments", ["user_id"])
    op.create_index("ix_comments_reel_id", "comments", ["reel_id"])


def downgrade() -> None:
    op.drop_index("ix_comments_reel_id", table_name="comments")
    op.drop_index("ix_comments_user_id", table_name="comments")
    op.drop_table("comments")
    op.drop_index("ix_reels_user_id", table_name="reels")
    op.drop_table("reels")
