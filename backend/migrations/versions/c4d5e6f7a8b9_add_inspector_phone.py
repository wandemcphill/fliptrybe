"""add inspector profile phone

Revision ID: c4d5e6f7a8b9
Revises: b7c8d9e0f1a2
Create Date: 2026-02-04 03:10:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "c4d5e6f7a8b9"
down_revision = "b7c8d9e0f1a2"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("inspector_profiles", schema=None) as batch_op:
        batch_op.add_column(sa.Column("phone", sa.String(length=32), nullable=True))
        batch_op.create_index(batch_op.f("ix_inspector_profiles_phone"), ["phone"], unique=False)


def downgrade():
    with op.batch_alter_table("inspector_profiles", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_inspector_profiles_phone"))
        batch_op.drop_column("phone")
