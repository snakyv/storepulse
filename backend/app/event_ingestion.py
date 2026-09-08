from dataclasses import dataclass
from datetime import datetime
from typing import Literal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import PosEvent, Product, Store
from app.schemas import SaleEventCreate


class UnknownStoreError(ValueError):
    pass


class UnknownProductError(ValueError):
    pass


class EventConflictError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class EventIngestionResult:
    event_id: UUID
    status: Literal["accepted", "duplicate"]
    received_at: datetime


async def _find_store(session: AsyncSession, store_code: str) -> Store:
    result = await session.execute(select(Store).where(Store.code == store_code))
    store = result.scalar_one_or_none()
    if store is None:
        raise UnknownStoreError(store_code)
    return store


async def _find_product(session: AsyncSession, product_sku: str) -> Product:
    result = await session.execute(select(Product).where(Product.sku == product_sku))
    product = result.scalar_one_or_none()
    if product is None:
        raise UnknownProductError(product_sku)
    return product


def _matches_sale_payload(
    existing: PosEvent,
    *,
    store_id: UUID,
    product_id: UUID,
    payload: SaleEventCreate,
) -> bool:
    return (
        existing.store_id == store_id
        and existing.product_id == product_id
        and existing.event_type == "SALE"
        and existing.quantity == payload.quantity
        and existing.amount_cents == payload.amount_cents
        and existing.occurred_at == payload.occurred_at
        and existing.original_event_id is None
        and existing.source_instance == payload.source_instance
        and existing.metadata_json == payload.metadata
        and existing.note == payload.note
    )


async def _classify_existing_event(
    session: AsyncSession,
    *,
    payload: SaleEventCreate,
    store: Store | None = None,
    product: Product | None = None,
) -> EventIngestionResult:
    existing = await session.get(PosEvent, payload.event_id)
    if existing is None:
        raise RuntimeError("event conflict was reported but the existing row is not visible")

    if store is None:
        stored_store = await session.get(Store, existing.store_id)
        if stored_store is None:
            raise RuntimeError("stored event references a missing store")
        store_matches = stored_store.code == payload.store_code
        store_id = stored_store.id
    else:
        store_matches = existing.store_id == store.id
        store_id = store.id

    if product is None:
        stored_product = await session.get(Product, existing.product_id)
        if stored_product is None:
            raise RuntimeError("stored event references a missing product")
        product_matches = stored_product.sku == payload.product_sku
        product_id = stored_product.id
    else:
        product_matches = existing.product_id == product.id
        product_id = product.id

    if not (
        store_matches
        and product_matches
        and _matches_sale_payload(
            existing,
            store_id=store_id,
            product_id=product_id,
            payload=payload,
        )
    ):
        raise EventConflictError(str(payload.event_id))

    return EventIngestionResult(
        event_id=existing.event_id,
        status="duplicate",
        received_at=existing.received_at,
    )


async def _classify_existing_and_rollback(
    session: AsyncSession,
    *,
    payload: SaleEventCreate,
    store: Store | None = None,
    product: Product | None = None,
) -> EventIngestionResult:
    try:
        return await _classify_existing_event(
            session,
            payload=payload,
            store=store,
            product=product,
        )
    finally:
        await session.rollback()


async def ingest_sale_event(
    session: AsyncSession,
    payload: SaleEventCreate,
) -> EventIngestionResult:
    """Persist one SALE event with PostgreSQL-authoritative idempotency."""
    existing = await session.get(PosEvent, payload.event_id)
    if existing is not None:
        return await _classify_existing_and_rollback(session, payload=payload)

    store = await _find_store(session, payload.store_code)
    product = await _find_product(session, payload.product_sku)

    statement = (
        insert(PosEvent)
        .values(
            event_id=payload.event_id,
            store_id=store.id,
            product_id=product.id,
            event_type="SALE",
            quantity=payload.quantity,
            amount_cents=payload.amount_cents,
            occurred_at=payload.occurred_at,
            original_event_id=None,
            source_instance=payload.source_instance,
            metadata_json=payload.metadata,
            note=payload.note,
        )
        .on_conflict_do_nothing(index_elements=[PosEvent.event_id])
        .returning(PosEvent.received_at)
    )
    insert_result = await session.execute(statement)
    received_at = insert_result.scalar_one_or_none()

    if received_at is None:
        return await _classify_existing_and_rollback(
            session,
            payload=payload,
            store=store,
            product=product,
        )

    store.last_seen_at = received_at
    await session.commit()
    return EventIngestionResult(
        event_id=payload.event_id,
        status="accepted",
        received_at=received_at,
    )
