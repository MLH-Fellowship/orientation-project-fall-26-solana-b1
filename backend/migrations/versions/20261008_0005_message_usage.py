"""Add token counts to messages."""

from alembic import op
import sqlalchemy as sa

revision = "20261008_0005"
down_revision = "20261008_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("messages") as batch_op:
        batch_op.add_column(sa.Column("prompt_tokens", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("completion_tokens", sa.Integer(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("messages") as batch_op:
        batch_op.drop_column("completion_tokens")
        batch_op.drop_column("prompt_tokens")
