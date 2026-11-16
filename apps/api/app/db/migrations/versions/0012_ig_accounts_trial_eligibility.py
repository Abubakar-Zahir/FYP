"""add ig_accounts.trial_reels_eligible

Revision ID: 0012
Revises: 0011
"""

import sqlalchemy as sa
from alembic import op

revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("ig_accounts") as batch:
        batch.add_column(sa.Column("trial_reels_eligible", sa.Boolean(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("ig_accounts") as batch:
        batch.drop_column("trial_reels_eligible")
