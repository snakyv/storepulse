"""Add database-level refund reference invariants.

Revision ID: 20260908_0002
Revises: 20260908_0001
Create Date: 2026-09-08
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260908_0002"
down_revision: str | None = "20260908_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_check_constraint(
        "ck_pos_events_original_reference",
        "pos_events",
        "(event_type = 'SALE' AND original_event_id IS NULL) "
        "OR (event_type = 'REFUND' AND original_event_id IS NOT NULL)",
    )
    op.create_check_constraint(
        "ck_pos_events_not_self_reference",
        "pos_events",
        "original_event_id IS NULL OR original_event_id <> event_id",
    )


def downgrade() -> None:
    op.drop_constraint("ck_pos_events_not_self_reference", "pos_events", type_="check")
    op.drop_constraint("ck_pos_events_original_reference", "pos_events", type_="check")
