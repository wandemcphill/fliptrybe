"""pricing fields and payout fees

Revision ID: b5f7e2d8c1a4
Revises: c5c9b2855c3a
Create Date: 2026-02-04 10:20:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b5f7e2d8c1a4'
down_revision = 'c5c9b2855c3a'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('listings', schema=None) as batch_op:
        batch_op.add_column(sa.Column('base_price', sa.Float(), nullable=False, server_default='0.0'))
        batch_op.add_column(sa.Column('platform_fee', sa.Float(), nullable=False, server_default='0.0'))
        batch_op.add_column(sa.Column('final_price', sa.Float(), nullable=False, server_default='0.0'))

    with op.batch_alter_table('shortlets', schema=None) as batch_op:
        batch_op.add_column(sa.Column('base_price', sa.Float(), nullable=False, server_default='0.0'))
        batch_op.add_column(sa.Column('platform_fee', sa.Float(), nullable=False, server_default='0.0'))
        batch_op.add_column(sa.Column('final_price', sa.Float(), nullable=False, server_default='0.0'))

    with op.batch_alter_table('merchant_profiles', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_top_tier', sa.Boolean(), nullable=False, server_default=sa.text('0')))

    with op.batch_alter_table('payout_requests', schema=None) as batch_op:
        batch_op.add_column(sa.Column('fee_amount', sa.Float(), nullable=False, server_default='0.0'))
        batch_op.add_column(sa.Column('net_amount', sa.Float(), nullable=False, server_default='0.0'))
        batch_op.add_column(sa.Column('speed', sa.String(length=16), nullable=False, server_default='standard'))


def downgrade():
    with op.batch_alter_table('payout_requests', schema=None) as batch_op:
        batch_op.drop_column('speed')
        batch_op.drop_column('net_amount')
        batch_op.drop_column('fee_amount')

    with op.batch_alter_table('merchant_profiles', schema=None) as batch_op:
        batch_op.drop_column('is_top_tier')

    with op.batch_alter_table('shortlets', schema=None) as batch_op:
        batch_op.drop_column('final_price')
        batch_op.drop_column('platform_fee')
        batch_op.drop_column('base_price')

    with op.batch_alter_table('listings', schema=None) as batch_op:
        batch_op.drop_column('final_price')
        batch_op.drop_column('platform_fee')
        batch_op.drop_column('base_price')
