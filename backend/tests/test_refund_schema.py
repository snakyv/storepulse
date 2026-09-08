from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas import RefundEventCreate


def _valid_refund_fields() -> dict[str, object]:
    return {
        "event_id": uuid4(),
        "store_code": "MAD-MADRID",
        "product_sku": "COFFEE-001",
        "event_type": "REFUND",
        "quantity": 1,
        "amount_cents": 400,
        "occurred_at": datetime.now(UTC),
        "original_event_id": uuid4(),
        "source_instance": "pytest:refund-schema",
    }


def test_refund_schema_accepts_timezone_aware_refund() -> None:
    event = RefundEventCreate(**_valid_refund_fields())
    assert event.event_type == "REFUND"
    assert event.occurred_at.tzinfo is not None


def test_refund_schema_requires_original_event_id() -> None:
    payload = _valid_refund_fields()
    del payload["original_event_id"]

    with pytest.raises(ValidationError):
        RefundEventCreate(**payload)


def test_refund_schema_requires_positive_strict_integers() -> None:
    zero_amount = _valid_refund_fields()
    zero_amount["amount_cents"] = 0
    boolean_quantity = _valid_refund_fields()
    boolean_quantity["quantity"] = True

    with pytest.raises(ValidationError):
        RefundEventCreate(**zero_amount)
    with pytest.raises(ValidationError):
        RefundEventCreate(**boolean_quantity)


def test_refund_schema_rejects_naive_timestamp_and_sale_type() -> None:
    naive = _valid_refund_fields()
    naive["occurred_at"] = datetime(2026, 9, 8, 20, 30)
    sale = _valid_refund_fields()
    sale["event_type"] = "SALE"

    with pytest.raises(ValidationError):
        RefundEventCreate(**naive)
    with pytest.raises(ValidationError):
        RefundEventCreate(**sale)


def test_refund_schema_forbids_unknown_fields() -> None:
    payload = _valid_refund_fields()
    payload["unexpected"] = "value"

    with pytest.raises(ValidationError):
        RefundEventCreate(**payload)
