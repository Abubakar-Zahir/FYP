"""create scripts table

Revision ID: 0007
Revises: 0006
"""

import sqlalchemy as sa
from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "scripts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("template_id", sa.Uuid(), nullable=False),
        sa.Column("topic", sa.Text(), nullable=False),
        sa.Column("language", sa.String(length=20), nullable=False),
        sa.Column("hooks", sa.JSON(), nullable=True),
        sa.Column("angles", sa.JSON(), nullable=True),
        sa.Column("body", sa.JSON(), nullable=True),
        sa.Column("model_version", sa.String(length=200), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["template_id"], ["dna_records.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_scripts_user_id", "scripts", ["user_id"])
    op.create_index("ix_scripts_template_id", "scripts", ["template_id"])


def downgrade() -> None:
    op.drop_index("ix_scripts_template_id", table_name="scripts")
    op.drop_index("ix_scripts_user_id", table_name="scripts")
    op.drop_table("scripts")
