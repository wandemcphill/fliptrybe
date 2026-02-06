"""shortlet owner + role change admin note + moneybox index

Revision ID: b7c8d9e0f1a2
Revises: a3b4c5d6e7f9
Create Date: 2026-02-04 02:15:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b7c8d9e0f1a2'
down_revision = 'a3b4c5d6e7f9'
branch_labels = None
depends_on = None


def upgrade():
    try:
        op.execute("DROP TABLE IF EXISTS _alembic_tmp_shortlets")
    except Exception:
        pass
    try:
        op.execute("DROP TABLE IF EXISTS _alembic_tmp_orders")
    except Exception:
        pass
    with op.batch_alter_table('shortlets', schema=None) as batch_op:
        batch_op.add_column(sa.Column('owner_id', sa.Integer(), nullable=True))
        batch_op.create_index(batch_op.f('ix_shortlets_owner_id'), ['owner_id'], unique=False)
        batch_op.create_foreign_key('fk_shortlets_owner_id_users', 'users', ['owner_id'], ['id'])

    with op.batch_alter_table('orders', schema=None) as batch_op:
        batch_op.add_column(sa.Column('inspection_fee', sa.Float(), nullable=True, server_default='0'))
    try:
        op.execute("UPDATE orders SET inspection_fee = 0 WHERE inspection_fee IS NULL")
    except Exception:
        pass
    with op.batch_alter_table('orders', schema=None) as batch_op:
        batch_op.alter_column('inspection_fee', nullable=False, server_default=None)

    with op.batch_alter_table('role_change_requests', schema=None) as batch_op:
        batch_op.add_column(sa.Column('admin_note', sa.String(length=400), nullable=True))

    with op.batch_alter_table('moneybox_ledger', schema=None) as batch_op:
        batch_op.create_index('ix_moneybox_ledger_account_created', ['account_id', 'created_at'], unique=False)


def downgrade():
    with op.batch_alter_table('moneybox_ledger', schema=None) as batch_op:
        batch_op.drop_index('ix_moneybox_ledger_account_created')

    with op.batch_alter_table('role_change_requests', schema=None) as batch_op:
        batch_op.drop_column('admin_note')

    with op.batch_alter_table('orders', schema=None) as batch_op:
        batch_op.drop_column('inspection_fee')

    with op.batch_alter_table('shortlets', schema=None) as batch_op:
        batch_op.drop_constraint('fk_shortlets_owner_id_users', type_='foreignkey')
        batch_op.drop_index(batch_op.f('ix_shortlets_owner_id'))
        batch_op.drop_column('owner_id')
