"""create dna_records table and add jobs.subject_id

Revision ID: 0006
Revises: 0005
"""

import sqlalchemy as sa
from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("jobs", sa.Column("subject_id", sa.Uuid(), nullable=True))
    op.create_table(
        "dna_records",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("reel_id", sa.Uuid(), nullable=False),
        sa.Column("schema_version", sa.String(length=10), nullable=False),
        sa.Column("hook_type", sa.String(length=30), nullable=False),
        sa.Column("hook_text", sa.Text(), nullable=False),
        sa.Column("pacing_cuts_per_10s", sa.Float(), nullable=False),
        sa.Column("length_s", sa.Float(), nullable=False),
        sa.Column("cta", sa.Text(), nullable=False),
        sa.Column("transcript", sa.Text(), nullable=False),
        sa.Column("record", sa.JSON(), nullable=False),
        sa.Column("model_version", sa.String(length=200), nullable=False),
        sa.Column("is_template", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["reel_id"], ["reels.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_dna_records_user_id", "dna_records", ["user_id"])
    op.create_index("ix_dna_records_reel_id", "dna_records", ["reel_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_dna_records_reel_id", table_name="dna_records")
    op.drop_index("ix_dna_records_user_id", table_name="dna_records")
    op.drop_table("dna_records")
    op.drop_column("jobs", "subject_id")
