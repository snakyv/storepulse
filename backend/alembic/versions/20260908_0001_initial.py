"""Initial StorePulse domain schema.

Revision ID: 20260908_0001
Revises: None
Create Date: 2026-09-08
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260908_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "stores",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("code", sa.String(length=40), nullable=False),
        sa.Column("timezone", sa.String(length=80), nullable=False),
        sa.Column("daily_target_cents", sa.BigInteger(), nullable=False),
        sa.Column("responsible_name", sa.String(length=120), nullable=False),
        sa.Column("responsible_email", sa.String(length=254), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("daily_target_cents >= 0", name="ck_stores_daily_target_nonnegative"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_stores_code", "stores", ["code"], unique=True)

    op.create_table(
        "products",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sku", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("category", sa.String(length=120), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("sku"),
    )

    op.create_table(
        "pos_events",
        sa.Column("event_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("store_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(length=16), nullable=False),
        sa.Column("quantity", sa.BigInteger(), nullable=False),
        sa.Column("amount_cents", sa.BigInteger(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("original_event_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("source_instance", sa.String(length=120), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.CheckConstraint("event_type IN ('SALE', 'REFUND')", name="ck_pos_events_type"),
        sa.CheckConstraint("quantity > 0", name="ck_pos_events_quantity_positive"),
        sa.CheckConstraint("amount_cents > 0", name="ck_pos_events_amount_positive"),
        sa.ForeignKeyConstraint(["original_event_id"], ["pos_events.event_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["store_id"], ["stores.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("event_id"),
    )
    op.create_index("ix_pos_events_store_id", "pos_events", ["store_id"], unique=False)
    op.create_index("ix_pos_events_product_id", "pos_events", ["product_id"], unique=False)
    op.create_index("ix_pos_events_occurred_at", "pos_events", ["occurred_at"], unique=False)
    op.create_index("ix_pos_events_original_event_id", "pos_events", ["original_event_id"], unique=False)
    op.create_index("ix_pos_events_store_occurred", "pos_events", ["store_id", "occurred_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_pos_events_store_occurred", table_name="pos_events")
    op.drop_index("ix_pos_events_original_event_id", table_name="pos_events")
    op.drop_index("ix_pos_events_occurred_at", table_name="pos_events")
    op.drop_index("ix_pos_events_product_id", table_name="pos_events")
    op.drop_index("ix_pos_events_store_id", table_name="pos_events")
    op.drop_table("pos_events")
    op.drop_table("products")
    op.drop_index("ix_stores_code", table_name="stores")
    op.drop_table("stores")
