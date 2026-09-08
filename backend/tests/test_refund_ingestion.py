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

TEST_SOURCE_PREFIX = "pytest:refund-ingestion:"


def _sale_payload(
    *,
    event_id: UUID | None = None,
    quantity: int = 2,
    amount_cents: int = 1000,
    store_code: str = "MAD-MADRID",
    product_sku: str = "COFFEE-001",
) -> dict[str, Any]:
    return {
        "event_id": str(event_id or uuid4()),
        "store_code": store_code,
        "product_sku": product_sku,
        "event_type": "SALE",
        "quantity": quantity,
        "amount_cents": amount_cents,
        "occurred_at": datetime.now(UTC).isoformat(),
        "source_instance": f"{TEST_SOURCE_PREFIX}sale:{uuid4()}",
        "metadata": {"origin": "refund-test"},
        "note": "refund-test-sale",
    }


def _refund_payload(
    original_event_id: UUID,
    *,
    event_id: UUID | None = None,
    quantity: int = 1,
    amount_cents: int = 400,
    occurred_at: datetime | None = None,
    store_code: str = "MAD-MADRID",
    product_sku: str = "COFFEE-001",
) -> dict[str, Any]:
    return {
        "event_id": str(event_id or uuid4()),
        "store_code": store_code,
        "product_sku": product_sku,
        "event_type": "REFUND",
        "quantity": quantity,
        "amount_cents": amount_cents,
        "occurred_at": (occurred_at or datetime.now(UTC)).isoformat(),
        "original_event_id": str(original_event_id),
        "source_instance": f"{TEST_SOURCE_PREFIX}refund:{uuid4()}",
        "metadata": {"reason": "customer-return"},
        "note": "refund-test-refund",
    }


@pytest_asyncio.fixture(autouse=True, loop_scope="session")
async def isolate_refund_ingestion_test_state() -> AsyncIterator[None]:
    async with get_session_factory()() as session:
        await session.execute(
            delete(PosEvent).where(
                PosEvent.source_instance.like(f"{TEST_SOURCE_PREFIX}%"),
                PosEvent.event_type == "REFUND",
            )
        )
        await session.execute(
            delete(PosEvent).where(PosEvent.source_instance.like(f"{TEST_SOURCE_PREFIX}%"))
        )
        store_rows = (await session.execute(select(Store.id, Store.last_seen_at))).all()
        original_last_seen = {store_id: last_seen for store_id, last_seen in store_rows}
        await session.commit()

    yield

    async with get_session_factory()() as session:
        await session.execute(
            delete(PosEvent).where(
                PosEvent.source_instance.like(f"{TEST_SOURCE_PREFIX}%"),
                PosEvent.event_type == "REFUND",
            )
        )
        await session.execute(
            delete(PosEvent).where(PosEvent.source_instance.like(f"{TEST_SOURCE_PREFIX}%"))
        )
        for store_id, last_seen_at in original_last_seen.items():
            await session.execute(
                update(Store).where(Store.id == store_id).values(last_seen_at=last_seen_at)
            )
        await session.commit()


async def _post(client: httpx.AsyncClient, payload: dict[str, Any]) -> httpx.Response:
    return await client.post("/api/v1/events", json=payload)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_partial_refund_is_persisted_and_links_original_sale() -> None:
    sale = _sale_payload(quantity=2, amount_cents=1000)
    sale_id = UUID(sale["event_id"])
    refund = _refund_payload(sale_id, quantity=1, amount_cents=400)
    refund_id = UUID(refund["event_id"])

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        sale_response = await _post(client, sale)
        refund_response = await _post(client, refund)

    assert sale_response.status_code == 201
    assert refund_response.status_code == 201
    assert refund_response.json()["status"] == "accepted"

    async with get_session_factory()() as session:
        stored = await session.get(PosEvent, refund_id)
        store = (
            await session.execute(select(Store).where(Store.code == refund["store_code"]))
        ).scalar_one()

    assert stored is not None
    assert stored.event_type == "REFUND"
    assert stored.original_event_id == sale_id
    assert stored.quantity == 1
    assert stored.amount_cents == 400
    assert store.last_seen_at == stored.received_at


@pytest.mark.integration
@pytest.mark.asyncio
async def test_exact_refund_duplicate_returns_200_without_second_row() -> None:
    sale = _sale_payload()
    sale_id = UUID(sale["event_id"])
    refund = _refund_payload(sale_id)
    refund_id = UUID(refund["event_id"])

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        assert (await _post(client, sale)).status_code == 201
        first = await _post(client, refund)
        duplicate = await _post(client, refund)

    assert first.status_code == 201
    assert duplicate.status_code == 200
    assert duplicate.json()["status"] == "duplicate"
    assert duplicate.json()["received_at"] == first.json()["received_at"]

    async with get_session_factory()() as session:
        count = (
            await session.execute(
                select(func.count()).select_from(PosEvent).where(PosEvent.event_id == refund_id)
            )
        ).scalar_one()

    assert count == 1


@pytest.mark.integration
@pytest.mark.asyncio
async def test_refund_same_event_id_with_different_payload_returns_409() -> None:
    sale = _sale_payload()
    sale_id = UUID(sale["event_id"])
    refund = _refund_payload(sale_id, amount_cents=400)
    conflicting = dict(refund)
    conflicting["amount_cents"] = 500

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        assert (await _post(client, sale)).status_code == 201
        accepted = await _post(client, refund)
        conflict = await _post(client, conflicting)

    assert accepted.status_code == 201
    assert conflict.status_code == 409
    assert conflict.json() == {"detail": "event_id already exists with different payload"}


@pytest.mark.integration
@pytest.mark.asyncio
async def test_existing_refund_id_conflict_precedes_new_original_validation() -> None:
    sale = _sale_payload()
    sale_id = UUID(sale["event_id"])
    refund = _refund_payload(sale_id, amount_cents=400)
    conflicting = dict(refund)
    conflicting["original_event_id"] = str(uuid4())

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        assert (await _post(client, sale)).status_code == 201
        assert (await _post(client, refund)).status_code == 201
        response = await _post(client, conflicting)

    assert response.status_code == 409
    assert response.json() == {"detail": "event_id already exists with different payload"}


@pytest.mark.integration
@pytest.mark.asyncio
async def test_missing_original_sale_returns_404() -> None:
    refund = _refund_payload(uuid4())

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await _post(client, refund)

    assert response.status_code == 404
    assert response.json() == {"detail": "original sale not found"}


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("field", "value", "expected_detail"),
    [
        ("store_code", "MAD-LONDON", "refund store must match original sale"),
        ("product_sku", "TEA-001", "refund product must match original sale"),
    ],
)
async def test_refund_store_and_product_must_match_original_sale(
    field: str,
    value: str,
    expected_detail: str,
) -> None:
    sale = _sale_payload()
    sale_id = UUID(sale["event_id"])
    refund = _refund_payload(sale_id)
    refund[field] = value

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        assert (await _post(client, sale)).status_code == 201
        response = await _post(client, refund)

    assert response.status_code == 422
    assert response.json() == {"detail": expected_detail}


@pytest.mark.integration
@pytest.mark.asyncio
async def test_refund_cannot_reference_another_refund() -> None:
    sale = _sale_payload(quantity=2, amount_cents=1000)
    sale_id = UUID(sale["event_id"])
    first_refund = _refund_payload(sale_id, quantity=1, amount_cents=400)
    first_refund_id = UUID(first_refund["event_id"])
    chained_refund = _refund_payload(first_refund_id, quantity=1, amount_cents=100)

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        assert (await _post(client, sale)).status_code == 201
        assert (await _post(client, first_refund)).status_code == 201
        response = await _post(client, chained_refund)

    assert response.status_code == 422
    assert response.json() == {"detail": "original_event_id must reference a SALE"}


@pytest.mark.integration
@pytest.mark.asyncio
async def test_cumulative_partial_refunds_can_exactly_reach_sale_limits() -> None:
    sale = _sale_payload(quantity=2, amount_cents=1000)
    sale_id = UUID(sale["event_id"])
    first_refund = _refund_payload(sale_id, quantity=1, amount_cents=400)
    second_refund = _refund_payload(sale_id, quantity=1, amount_cents=600)

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        assert (await _post(client, sale)).status_code == 201
        first = await _post(client, first_refund)
        second = await _post(client, second_refund)

    assert first.status_code == 201
    assert second.status_code == 201


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("first_quantity", "first_amount", "next_quantity", "next_amount", "detail"),
    [
        (1, 400, 2, 100, "refund exceeds remaining sale quantity"),
        (1, 700, 1, 400, "refund exceeds remaining sale amount"),
    ],
)
async def test_cumulative_refund_cannot_exceed_sale_limits(
    first_quantity: int,
    first_amount: int,
    next_quantity: int,
    next_amount: int,
    detail: str,
) -> None:
    sale = _sale_payload(quantity=2, amount_cents=1000)
    sale_id = UUID(sale["event_id"])
    first_refund = _refund_payload(
        sale_id,
        quantity=first_quantity,
        amount_cents=first_amount,
    )
    next_refund = _refund_payload(
        sale_id,
        quantity=next_quantity,
        amount_cents=next_amount,
    )

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        assert (await _post(client, sale)).status_code == 201
        assert (await _post(client, first_refund)).status_code == 201
        rejected = await _post(client, next_refund)

    assert rejected.status_code == 409
    assert rejected.json() == {"detail": detail}


@pytest.mark.integration
@pytest.mark.asyncio
async def test_late_refund_preserves_its_occurred_at() -> None:
    sale = _sale_payload()
    sale_id = UUID(sale["event_id"])
    occurred_at = datetime.now(UTC) - timedelta(hours=3)
    refund = _refund_payload(sale_id, occurred_at=occurred_at)
    refund_id = UUID(refund["event_id"])

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        assert (await _post(client, sale)).status_code == 201
        response = await _post(client, refund)

    assert response.status_code == 201
    async with get_session_factory()() as session:
        stored = await session.get(PosEvent, refund_id)

    assert stored is not None
    assert stored.occurred_at == occurred_at
    assert stored.received_at > stored.occurred_at


@pytest.mark.integration
@pytest.mark.asyncio
async def test_concurrent_identical_refunds_create_exactly_one_row() -> None:
    sale = _sale_payload(quantity=2, amount_cents=1000)
    sale_id = UUID(sale["event_id"])
    refund = _refund_payload(sale_id, quantity=1, amount_cents=400)
    refund_id = UUID(refund["event_id"])
    request_count = 8

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        assert (await _post(client, sale)).status_code == 201
        responses = await asyncio.gather(*(_post(client, refund) for _ in range(request_count)))

    assert [response.status_code for response in responses].count(201) == 1
    assert [response.status_code for response in responses].count(200) == request_count - 1

    async with get_session_factory()() as session:
        count = (
            await session.execute(
                select(func.count()).select_from(PosEvent).where(PosEvent.event_id == refund_id)
            )
        ).scalar_one()

    assert count == 1


@pytest.mark.integration
@pytest.mark.asyncio
async def test_concurrent_refunds_cannot_over_refund_amount() -> None:
    sale = _sale_payload(quantity=2, amount_cents=1000)
    sale_id = UUID(sale["event_id"])
    first_refund = _refund_payload(sale_id, quantity=1, amount_cents=700)
    second_refund = _refund_payload(sale_id, quantity=1, amount_cents=700)

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        assert (await _post(client, sale)).status_code == 201
        first_response, second_response = await asyncio.gather(
            _post(client, first_refund),
            _post(client, second_refund),
        )

    assert sorted([first_response.status_code, second_response.status_code]) == [201, 409]
    rejected = first_response if first_response.status_code == 409 else second_response
    assert rejected.json() == {"detail": "refund exceeds remaining sale amount"}

    async with get_session_factory()() as session:
        refund_count, refunded_amount = (
            await session.execute(
                select(
                    func.count(),
                    func.coalesce(func.sum(PosEvent.amount_cents), 0),
                ).where(
                    PosEvent.event_type == "REFUND",
                    PosEvent.original_event_id == sale_id,
                )
            )
        ).one()

    assert refund_count == 1
    assert refunded_amount == 700


@pytest.mark.integration
@pytest.mark.asyncio
async def test_concurrent_refunds_cannot_over_refund_quantity() -> None:
    sale = _sale_payload(quantity=1, amount_cents=1000)
    sale_id = UUID(sale["event_id"])
    first_refund = _refund_payload(sale_id, quantity=1, amount_cents=400)
    second_refund = _refund_payload(sale_id, quantity=1, amount_cents=400)

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        assert (await _post(client, sale)).status_code == 201
        first_response, second_response = await asyncio.gather(
            _post(client, first_refund),
            _post(client, second_refund),
        )

    assert sorted([first_response.status_code, second_response.status_code]) == [201, 409]
    rejected = first_response if first_response.status_code == 409 else second_response
    assert rejected.json() == {"detail": "refund exceeds remaining sale quantity"}

    async with get_session_factory()() as session:
        refund_count = (
            await session.execute(
                select(func.count()).where(
                    PosEvent.event_type == "REFUND",
                    PosEvent.original_event_id == sale_id,
                )
            )
        ).scalar_one()

    assert refund_count == 1
