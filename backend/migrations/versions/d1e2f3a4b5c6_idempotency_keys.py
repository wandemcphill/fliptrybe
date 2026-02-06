"""idempotency keys for ledger and timeline

Revision ID: d1e2f3a4b5c6
Revises: c4d5e6f7a8b9
Create Date: 2026-02-04 02:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = 'd1e2f3a4b5c6'
down_revision = 'c4d5e6f7a8b9'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    insp = inspect(bind)

    def _col_exists(table_name: str, col: str) -> bool:
        try:
            cols = [c["name"] for c in insp.get_columns(table_name)]
            return col in cols
        except Exception:
            return False

    def _index_exists(table_name: str, idx_name: str) -> bool:
        try:
            idxs = [i.get("name") for i in insp.get_indexes(table_name)]
            return idx_name in idxs
        except Exception:
            return False

    if not _col_exists("moneybox_ledger", "idempotency_key"):
        with op.batch_alter_table('moneybox_ledger', schema=None) as batch_op:
            batch_op.add_column(sa.Column('idempotency_key', sa.String(length=160), nullable=True))
    if not _index_exists("moneybox_ledger", "uq_moneybox_ledger_idempotency_key"):
        with op.batch_alter_table('moneybox_ledger', schema=None) as batch_op:
            batch_op.create_index('uq_moneybox_ledger_idempotency_key', ['idempotency_key'], unique=True)

    if not _col_exists("wallet_txns", "idempotency_key"):
        with op.batch_alter_table('wallet_txns', schema=None) as batch_op:
            batch_op.add_column(sa.Column('idempotency_key', sa.String(length=160), nullable=True))
    if not _index_exists("wallet_txns", "uq_wallet_txns_idempotency_key"):
        with op.batch_alter_table('wallet_txns', schema=None) as batch_op:
            batch_op.create_index('uq_wallet_txns_idempotency_key', ['idempotency_key'], unique=True)

    if not _col_exists("order_events", "idempotency_key"):
        with op.batch_alter_table('order_events', schema=None) as batch_op:
            batch_op.add_column(sa.Column('idempotency_key', sa.String(length=160), nullable=True))
    if not _index_exists("order_events", "uq_order_events_idempotency_key"):
        with op.batch_alter_table('order_events', schema=None) as batch_op:
            batch_op.create_index('uq_order_events_idempotency_key', ['idempotency_key'], unique=True)


def downgrade():
    with op.batch_alter_table('order_events', schema=None) as batch_op:
        batch_op.drop_index('uq_order_events_idempotency_key')
        batch_op.drop_column('idempotency_key')

    with op.batch_alter_table('wallet_txns', schema=None) as batch_op:
        batch_op.drop_index('uq_wallet_txns_idempotency_key')
        batch_op.drop_column('idempotency_key')

    with op.batch_alter_table('moneybox_ledger', schema=None) as batch_op:
        batch_op.drop_index('uq_moneybox_ledger_idempotency_key')
        batch_op.drop_column('idempotency_key')
