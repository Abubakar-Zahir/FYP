"""create videos table

Revision ID: 0010
Revises: 0009
"""

import sqlalchemy as sa
from alembic import op

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "videos",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("source_r2_key", sa.String(length=300), nullable=False),
        sa.Column("output_r2_key", sa.String(length=300), nullable=True),
        sa.Column("duration_s", sa.Float(), nullable=True),
        sa.Column("removed_silence_s", sa.Float(), nullable=True),
        sa.Column("options", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_videos_user_id", "videos", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_videos_user_id", table_name="videos")
    op.drop_table("videos")
