"""Index messages by conversation."""

from alembic import op

revision = "20261005_0003"
down_revision = "20261003_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index("ix_messages_conversation_id", "messages", ["conversation_id"])


def downgrade() -> None:
    op.drop_index("ix_messages_conversation_id", table_name="messages")
