"""create experiments, variants, variant_insights and bandit_beliefs

Revision ID: 0011
Revises: 0010
"""

import sqlalchemy as sa
from alembic import op

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "experiments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("video_id", sa.Uuid(), nullable=False),
        sa.Column("script_id", sa.Uuid(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("winner_variant_id", sa.Uuid(), nullable=True),
        sa.Column("share_requested_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["video_id"], ["videos.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["script_id"], ["scripts.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_experiments_user_id", "experiments", ["user_id"])
    op.create_index("ix_experiments_video_id", "experiments", ["video_id"])
    op.create_table(
        "variants",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("experiment_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("label", sa.String(length=4), nullable=False),
        sa.Column("hook_line", sa.Text(), nullable=False),
        sa.Column("hook_style", sa.String(length=40), nullable=False),
        sa.Column("opener", sa.Text(), nullable=False),
        sa.Column("opener_type", sa.String(length=40), nullable=False),
        sa.Column("caption", sa.Text(), nullable=False),
        sa.Column("caption_length", sa.String(length=40), nullable=False),
        sa.Column("is_trial", sa.Boolean(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("r2_key", sa.String(length=300), nullable=True),
        sa.Column("ig_media_id", sa.String(length=64), nullable=True),
        sa.Column("permalink", sa.Text(), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error", sa.String(length=200), nullable=True),
        sa.ForeignKeyConstraint(["experiment_id"], ["experiments.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_variants_experiment_id", "variants", ["experiment_id"])
    op.create_index("ix_variants_user_id", "variants", ["user_id"])
    op.create_table(
        "variant_insights",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("variant_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("window", sa.String(length=8), nullable=False),
        sa.Column("views", sa.Integer(), nullable=True),
        sa.Column("reach", sa.Integer(), nullable=True),
        sa.Column("saves", sa.Integer(), nullable=True),
        sa.Column("shares", sa.Integer(), nullable=True),
        sa.Column("fetched_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["variant_id"], ["variants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("variant_id", "window", name="uq_variant_insights_window"),
    )
    op.create_index("ix_variant_insights_variant_id", "variant_insights", ["variant_id"])
    op.create_index("ix_variant_insights_user_id", "variant_insights", ["user_id"])
    op.create_table(
        "bandit_beliefs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("feature", sa.String(length=40), nullable=False),
        sa.Column("value", sa.String(length=40), nullable=False),
        sa.Column("alpha", sa.Float(), nullable=False),
        sa.Column("beta", sa.Float(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "feature", "value", name="uq_bandit_beliefs"),
    )
    op.create_index("ix_bandit_beliefs_user_id", "bandit_beliefs", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_bandit_beliefs_user_id", table_name="bandit_beliefs")
    op.drop_table("bandit_beliefs")
    op.drop_index("ix_variant_insights_user_id", table_name="variant_insights")
    op.drop_index("ix_variant_insights_variant_id", table_name="variant_insights")
    op.drop_table("variant_insights")
    op.drop_index("ix_variants_user_id", table_name="variants")
    op.drop_index("ix_variants_experiment_id", table_name="variants")
    op.drop_table("variants")
    op.drop_index("ix_experiments_video_id", table_name="experiments")
    op.drop_index("ix_experiments_user_id", table_name="experiments")
    op.drop_table("experiments")
