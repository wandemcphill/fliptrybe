"""add_order_secret_code_columns

Revision ID: 52713a9a384f
Revises: 6ef75d676939
Create Date: 2026-02-06 01:05:15.575383

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '52713a9a384f'
down_revision = '6ef75d676939'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    if "orders" not in tables:
        return

    cols = {c["name"] for c in inspector.get_columns("orders")}
    with op.batch_alter_table("orders", schema=None) as batch_op:
        if "pickup_code" not in cols:
            batch_op.add_column(sa.Column("pickup_code", sa.String(length=8), nullable=True))
        if "dropoff_code" not in cols:
            batch_op.add_column(sa.Column("dropoff_code", sa.String(length=8), nullable=True))
        if "pickup_code_attempts" not in cols:
            batch_op.add_column(sa.Column("pickup_code_attempts", sa.Integer(), nullable=False, server_default="0"))
        if "dropoff_code_attempts" not in cols:
            batch_op.add_column(sa.Column("dropoff_code_attempts", sa.Integer(), nullable=False, server_default="0"))
        if "pickup_confirmed_at" not in cols:
            batch_op.add_column(sa.Column("pickup_confirmed_at", sa.DateTime(), nullable=True))
        if "dropoff_confirmed_at" not in cols:
            batch_op.add_column(sa.Column("dropoff_confirmed_at", sa.DateTime(), nullable=True))


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    if "orders" not in tables:
        return

    cols = {c["name"] for c in inspector.get_columns("orders")}
    with op.batch_alter_table("orders", schema=None) as batch_op:
        if "dropoff_confirmed_at" in cols:
            batch_op.drop_column("dropoff_confirmed_at")
        if "pickup_confirmed_at" in cols:
            batch_op.drop_column("pickup_confirmed_at")
        if "dropoff_code_attempts" in cols:
            batch_op.drop_column("dropoff_code_attempts")
        if "pickup_code_attempts" in cols:
            batch_op.drop_column("pickup_code_attempts")
        if "dropoff_code" in cols:
            batch_op.drop_column("dropoff_code")
        if "pickup_code" in cols:
            batch_op.drop_column("pickup_code")
