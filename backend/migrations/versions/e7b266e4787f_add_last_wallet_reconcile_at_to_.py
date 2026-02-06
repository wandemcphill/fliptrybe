"""add last_wallet_reconcile_at to autopilot_settings

Revision ID: e7b266e4787f
Revises: 52713a9a384f
Create Date: 2026-02-06 03:52:03.067270

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e7b266e4787f'
down_revision = '52713a9a384f'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)
    if "autopilot_settings" not in insp.get_table_names():
        return
    cols = {c["name"] for c in insp.get_columns("autopilot_settings")}
    if "last_wallet_reconcile_at" in cols:
        return
    with op.batch_alter_table("autopilot_settings") as batch_op:
        batch_op.add_column(sa.Column("last_wallet_reconcile_at", sa.DateTime(), nullable=True))


def downgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)
    if "autopilot_settings" not in insp.get_table_names():
        return
    cols = {c["name"] for c in insp.get_columns("autopilot_settings")}
    if "last_wallet_reconcile_at" not in cols:
        return
    with op.batch_alter_table("autopilot_settings") as batch_op:
        batch_op.drop_column("last_wallet_reconcile_at")
