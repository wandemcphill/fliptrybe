"""add_users_phone_column

Revision ID: 6ef75d676939
Revises: 5b3fb793b136
Create Date: 2026-02-06 00:30:56.258816

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6ef75d676939'
down_revision = '5b3fb793b136'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    if "users" not in tables:
        return

    columns = {col["name"] for col in inspector.get_columns("users")}
    if "phone" in columns:
        return

    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.add_column(sa.Column("phone", sa.String(length=32), nullable=True))


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    if "users" not in tables:
        return

    columns = {col["name"] for col in inspector.get_columns("users")}
    if "phone" not in columns:
        return

    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_column("phone")
