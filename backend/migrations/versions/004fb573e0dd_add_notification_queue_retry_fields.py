"""add notification_queue retry fields

Revision ID: 004fb573e0dd
Revises: e7b266e4787f
Create Date: 2026-02-06 03:55:37.731060

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '004fb573e0dd'
down_revision = 'e7b266e4787f'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)
    if "notification_queue" not in insp.get_table_names():
        return
    cols = {c["name"] for c in insp.get_columns("notification_queue")}
    with op.batch_alter_table("notification_queue") as batch_op:
        if "attempt_count" not in cols:
            batch_op.add_column(sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"))
        if "max_attempts" not in cols:
            batch_op.add_column(sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="5"))
        if "next_attempt_at" not in cols:
            batch_op.add_column(sa.Column("next_attempt_at", sa.DateTime(), nullable=True))
        if "last_error" not in cols:
            batch_op.add_column(sa.Column("last_error", sa.String(length=240), nullable=True))
        if "dead_lettered_at" not in cols:
            batch_op.add_column(sa.Column("dead_lettered_at", sa.DateTime(), nullable=True))


def downgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)
    if "notification_queue" not in insp.get_table_names():
        return
    cols = {c["name"] for c in insp.get_columns("notification_queue")}
    with op.batch_alter_table("notification_queue") as batch_op:
        if "dead_lettered_at" in cols:
            batch_op.drop_column("dead_lettered_at")
        if "last_error" in cols:
            batch_op.drop_column("last_error")
        if "next_attempt_at" in cols:
            batch_op.drop_column("next_attempt_at")
        if "max_attempts" in cols:
            batch_op.drop_column("max_attempts")
        if "attempt_count" in cols:
            batch_op.drop_column("attempt_count")
