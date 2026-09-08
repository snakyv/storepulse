from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas import SaleEventCreate


def _valid_sale_fields() -> dict[str, object]:
    return {
        "event_id": uuid4(),
        "store_code": "MAD-MADRID",
        "product_sku": "COFFEE-001",
        "event_type": "SALE",
        "quantity": 1,
        "amount_cents": 100,
        "occurred_at": datetime.now(UTC),
        "source_instance": "pytest:schema",
    }


def test_sale_event_schema_accepts_timezone_aware_sale() -> None:
    event = SaleEventCreate(**_valid_sale_fields())
    assert event.event_type == "SALE"
    assert event.occurred_at.tzinfo is not None


def test_sale_event_schema_requires_positive_strict_integers() -> None:
    zero_quantity = _valid_sale_fields()
    zero_quantity["quantity"] = 0
    boolean_amount = _valid_sale_fields()
    boolean_amount["amount_cents"] = True

    with pytest.raises(ValidationError):
        SaleEventCreate(**zero_quantity)
    with pytest.raises(ValidationError):
        SaleEventCreate(**boolean_amount)


def test_sale_event_schema_rejects_naive_timestamp_and_refund_type() -> None:
    naive = _valid_sale_fields()
    naive["occurred_at"] = datetime(2026, 9, 8, 18, 30)
    refund = _valid_sale_fields()
    refund["event_type"] = "REFUND"

    with pytest.raises(ValidationError):
        SaleEventCreate(**naive)
    with pytest.raises(ValidationError):
        SaleEventCreate(**refund)


def test_sale_event_schema_forbids_unknown_fields() -> None:
    payload = _valid_sale_fields()
    payload["unexpected"] = "value"

    with pytest.raises(ValidationError):
        SaleEventCreate(**payload)
