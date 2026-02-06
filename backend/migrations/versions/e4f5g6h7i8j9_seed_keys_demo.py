"""seed keys for demo idempotency

Revision ID: e4f5g6h7i8j9
Revises: d1e2f3a4b5c6
Create Date: 2026-02-04 03:05:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = 'e4f5g6h7i8j9'
down_revision = 'd1e2f3a4b5c6'
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

    if not _col_exists("listings", "seed_key"):
        with op.batch_alter_table('listings', schema=None) as batch_op:
            batch_op.add_column(sa.Column('seed_key', sa.String(length=64), nullable=True))
    if not _index_exists("listings", "uq_listings_seed_key"):
        with op.batch_alter_table('listings', schema=None) as batch_op:
            batch_op.create_index('uq_listings_seed_key', ['seed_key'], unique=True)

    if not _col_exists("orders", "seed_key"):
        with op.batch_alter_table('orders', schema=None) as batch_op:
            batch_op.add_column(sa.Column('seed_key', sa.String(length=64), nullable=True))
    if not _index_exists("orders", "uq_orders_seed_key"):
        with op.batch_alter_table('orders', schema=None) as batch_op:
            batch_op.create_index('uq_orders_seed_key', ['seed_key'], unique=True)


def downgrade():
    with op.batch_alter_table('orders', schema=None) as batch_op:
        batch_op.drop_index('uq_orders_seed_key')
        batch_op.drop_column('seed_key')

    with op.batch_alter_table('listings', schema=None) as batch_op:
        batch_op.drop_index('uq_listings_seed_key')
        batch_op.drop_column('seed_key')
