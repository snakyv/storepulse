import asyncio
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import httpx
import pytest
import pytest_asyncio
from sqlalchemy import delete, func, select, update

from app.db import get_session_factory
from app.main import app
from app.models import PosEvent, Store

TEST_SOURCE_PREFIX = "pytest:sale-ingestion:"


def _sale_payload(
    *,
    event_id: UUID | None = None,
    amount_cents: int = 1598,
    occurred_at: datetime | None = None,
    store_code: str = "MAD-MADRID",
    product_sku: str = "COFFEE-001",
    source_instance: str | None = None,
) -> dict[str, Any]:
    event_id = event_id or uuid4()
    occurred_at = occurred_at or datetime.now(UTC)
    source_instance = source_instance or f"{TEST_SOURCE_PREFIX}{uuid4()}"
    return {
        "event_id": str(event_id),
        "store_code": store_code,
        "product_sku": product_sku,
        "event_type": "SALE",
        "quantity": 2,
        "amount_cents": amount_cents,
        "occurred_at": occurred_at.isoformat(),
        "source_instance": source_instance,
        "metadata": {"terminal": "POS-01", "cashier": "demo"},
        "note": "integration-test-sale",
    }


@pytest_asyncio.fixture(autouse=True, loop_scope="session")
async def isolate_sale_ingestion_test_state() -> AsyncIterator[None]:
    async with get_session_factory()() as session:
        await session.execute(
            delete(PosEvent).where(PosEvent.source_instance.like(f"{TEST_SOURCE_PREFIX}%"))
        )
        store_rows = (await session.execute(select(Store.id, Store.last_seen_at))).all()
        original_last_seen = {store_id: last_seen for store_id, last_seen in store_rows}
        await session.commit()

    yield

    async with get_session_factory()() as session:
        await session.execute(
            delete(PosEvent).where(PosEvent.source_instance.like(f"{TEST_SOURCE_PREFIX}%"))
        )
        for store_id, last_seen_at in original_last_seen.items():
            await session.execute(
                update(Store).where(Store.id == store_id).values(last_seen_at=last_seen_at)
            )
        await session.commit()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_sale_is_accepted_persisted_and_marks_store_seen() -> None:
    payload = _sale_payload()
    event_id = UUID(payload["event_id"])

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/events", json=payload)

    assert response.status_code == 201
    body = response.json()
    assert body["event_id"] == str(event_id)
    assert body["status"] == "accepted"

    async with get_session_factory()() as session:
        event = await session.get(PosEvent, event_id)
        store = (
            await session.execute(select(Store).where(Store.code == payload["store_code"]))
        ).scalar_one()

    assert event is not None
    assert event.event_type == "SALE"
    assert event.quantity == 2
    assert event.amount_cents == 1598
    assert event.original_event_id is None
    assert event.source_instance == payload["source_instance"]
    assert event.metadata_json == payload["metadata"]
    assert event.note == payload["note"]
    assert event.occurred_at == datetime.fromisoformat(payload["occurred_at"])
    assert event.received_at.tzinfo is not None
    assert store.last_seen_at == event.received_at


@pytest.mark.integration
@pytest.mark.asyncio
async def test_exact_duplicate_returns_200_without_second_row() -> None:
    payload = _sale_payload()
    event_id = UUID(payload["event_id"])

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        first = await client.post("/api/v1/events", json=payload)
        second = await client.post("/api/v1/events", json=payload)

    assert first.status_code == 201
    assert first.json()["status"] == "accepted"
    assert second.status_code == 200
    assert second.json()["status"] == "duplicate"
    assert second.json()["received_at"] == first.json()["received_at"]

    async with get_session_factory()() as session:
        count = (
            await session.execute(
                select(func.count()).select_from(PosEvent).where(PosEvent.event_id == event_id)
            )
        ).scalar_one()

    assert count == 1


@pytest.mark.integration
@pytest.mark.asyncio
async def test_same_event_id_with_different_payload_returns_409() -> None:
    event_id = uuid4()
    original = _sale_payload(event_id=event_id, amount_cents=1598)
    conflicting = dict(original)
    conflicting["amount_cents"] = 2598

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        accepted = await client.post("/api/v1/events", json=original)
        conflict = await client.post("/api/v1/events", json=conflicting)

    assert accepted.status_code == 201
    assert conflict.status_code == 409
    assert conflict.json() == {"detail": "event_id already exists with different payload"}

    async with get_session_factory()() as session:
        event = await session.get(PosEvent, event_id)

    assert event is not None
    assert event.amount_cents == 1598


@pytest.mark.integration
@pytest.mark.asyncio
async def test_existing_event_id_conflict_takes_precedence_over_new_reference_validation() -> None:
    event_id = uuid4()
    original = _sale_payload(event_id=event_id)
    conflicting = dict(original)
    conflicting["store_code"] = "DOES-NOT-EXIST"

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        accepted = await client.post("/api/v1/events", json=original)
        conflict = await client.post("/api/v1/events", json=conflicting)

    assert accepted.status_code == 201
    assert conflict.status_code == 409
    assert conflict.json() == {"detail": "event_id already exists with different payload"}


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("field", "value", "expected_detail"),
    [
        ("store_code", "DOES-NOT-EXIST", "unknown store"),
        ("product_sku", "DOES-NOT-EXIST", "unknown product"),
    ],
)
async def test_unknown_references_return_404(
    field: str,
    value: str,
    expected_detail: str,
) -> None:
    payload = _sale_payload()
    payload[field] = value

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/events", json=payload)

    assert response.status_code == 404
    assert response.json() == {"detail": expected_detail}


@pytest.mark.integration
@pytest.mark.asyncio
async def test_naive_occurred_at_is_rejected() -> None:
    payload = _sale_payload()
    payload["occurred_at"] = "2026-09-08T18:30:00"

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/events", json=payload)

    assert response.status_code == 422


@pytest.mark.integration
@pytest.mark.asyncio
async def test_refund_without_original_event_id_is_rejected() -> None:
    payload = _sale_payload()
    payload["event_type"] = "REFUND"

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/events", json=payload)

    assert response.status_code == 422


@pytest.mark.integration
@pytest.mark.asyncio
async def test_late_sale_preserves_occurred_at_instead_of_reception_time() -> None:
    occurred_at = datetime.now(UTC) - timedelta(hours=2, minutes=15)
    payload = _sale_payload(occurred_at=occurred_at)
    event_id = UUID(payload["event_id"])

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/events", json=payload)

    assert response.status_code == 201

    async with get_session_factory()() as session:
        event = await session.get(PosEvent, event_id)

    assert event is not None
    assert event.occurred_at == occurred_at
    assert event.received_at > event.occurred_at


@pytest.mark.integration
@pytest.mark.asyncio
async def test_concurrent_identical_requests_create_exactly_one_event() -> None:
    payload = _sale_payload()
    event_id = UUID(payload["event_id"])
    request_count = 8

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        responses = await asyncio.gather(
            *(client.post("/api/v1/events", json=payload) for _ in range(request_count))
        )

    assert [response.status_code for response in responses].count(201) == 1
    assert [response.status_code for response in responses].count(200) == request_count - 1
    assert [response.json()["status"] for response in responses].count("accepted") == 1
    assert [response.json()["status"] for response in responses].count("duplicate") == 7

    async with get_session_factory()() as session:
        count = (
            await session.execute(
                select(func.count()).select_from(PosEvent).where(PosEvent.event_id == event_id)
            )
        ).scalar_one()

    assert count == 1


@pytest.mark.integration
@pytest.mark.asyncio
async def test_concurrent_conflicting_payloads_resolve_to_one_accept_and_one_conflict() -> None:
    event_id = uuid4()
    first_payload = _sale_payload(event_id=event_id, amount_cents=1598)
    second_payload = dict(first_payload)
    second_payload["amount_cents"] = 2598

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        first_response, second_response = await asyncio.gather(
            client.post("/api/v1/events", json=first_payload),
            client.post("/api/v1/events", json=second_payload),
        )

    responses = [first_response, second_response]
    assert sorted(response.status_code for response in responses) == [201, 409]

    accepted_amount = 1598 if first_response.status_code == 201 else 2598
    async with get_session_factory()() as session:
        event = await session.get(PosEvent, event_id)

    assert event is not None
    assert event.amount_cents == accepted_amount
