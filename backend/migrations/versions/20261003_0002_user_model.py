"""Add users and optional conversation ownership."""

from alembic import op
import sqlalchemy as sa

revision = "20261003_0002"
down_revision = "20260929_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    with op.batch_alter_table("conversations") as batch_op:
        batch_op.add_column(sa.Column("user_id", sa.String(), nullable=True))
        batch_op.create_foreign_key("fk_conversations_user_id_users", "users", ["user_id"], ["id"])
        batch_op.create_index("ix_conversations_user_id", ["user_id"])


def downgrade() -> None:
    with op.batch_alter_table("conversations") as batch_op:
        batch_op.drop_index("ix_conversations_user_id")
        batch_op.drop_constraint("fk_conversations_user_id_users", type_="foreignkey")
        batch_op.drop_column("user_id")
    op.drop_table("users")
