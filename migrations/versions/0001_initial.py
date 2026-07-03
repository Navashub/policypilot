"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-07-03

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

user_role = postgresql.ENUM("owner", "admin", "member", name="userrole")
document_status = postgresql.ENUM("pending", "processing", "ready", "failed", name="documentstatus")


def upgrade() -> None:
    bind = op.get_bind()
    user_role.create(bind, checkfirst=True)
    document_status.create(bind, checkfirst=True)

    op.create_table(
        "orgs",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("plan", sa.String(50), nullable=False, server_default="free"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("org_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("orgs.id"), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("role", user_role, nullable=False, server_default="member"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "documents",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("org_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("orgs.id"), nullable=False),
        sa.Column("uploaded_by", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("filename", sa.String(500), nullable=False),
        sa.Column("status", document_status, nullable=False, server_default="pending"),
        sa.Column("chunks_created", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_documents_org_id", "documents", ["org_id"])

    op.create_table(
        "conversations",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("org_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("orgs.id"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False, server_default="New conversation"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_conversations_org_id", "conversations", ["org_id"])

    op.create_table(
        "messages",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column(
            "conversation_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("conversations.id"), nullable=False
        ),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("sources", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_messages_conversation_id", "messages", ["conversation_id"])

    op.create_table(
        "api_keys",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("org_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("orgs.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("key_hash", sa.String(255), nullable=False),
        sa.Column("key_prefix", sa.String(12), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_index("ix_api_keys_org_id", "api_keys", ["org_id"])

    op.create_table(
        "usage_events",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("org_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("orgs.id"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("tokens_used", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_usage_events_org_id", "usage_events", ["org_id"])
    op.create_index("ix_usage_events_created_at", "usage_events", ["created_at"])


def downgrade() -> None:
    op.drop_table("usage_events")
    op.drop_table("api_keys")
    op.drop_table("messages")
    op.drop_table("conversations")
    op.drop_table("documents")
    op.drop_table("users")
    op.drop_table("orgs")

    bind = op.get_bind()
    document_status.drop(bind, checkfirst=True)
    user_role.drop(bind, checkfirst=True)
