from dataclasses import dataclass
from datetime import datetime
from typing import Literal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import PosEvent, Product, Store
from app.schemas import EventCreate, RefundEventCreate, SaleEventCreate


class UnknownStoreError(ValueError):
    pass


class UnknownProductError(ValueError):
    pass


class EventConflictError(ValueError):
    pass


class OriginalSaleNotFoundError(ValueError):
    pass


class InvalidOriginalSaleError(ValueError):
    pass


class RefundReferenceMismatchError(ValueError):
    pass


class RefundLimitExceededError(ValueError):
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


def _payload_original_event_id(payload: EventCreate) -> UUID | None:
    if isinstance(payload, RefundEventCreate):
        return payload.original_event_id
    return None


def _matches_event_payload(
    existing: PosEvent,
    *,
    store_id: UUID,
    product_id: UUID,
    payload: EventCreate,
) -> bool:
    return (
        existing.store_id == store_id
        and existing.product_id == product_id
        and existing.event_type == payload.event_type
        and existing.quantity == payload.quantity
        and existing.amount_cents == payload.amount_cents
        and existing.occurred_at == payload.occurred_at
        and existing.original_event_id == _payload_original_event_id(payload)
        and existing.source_instance == payload.source_instance
        and existing.metadata_json == payload.metadata
        and existing.note == payload.note
    )


async def _classify_existing_event(
    session: AsyncSession,
    *,
    payload: EventCreate,
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
        and _matches_event_payload(
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
    payload: EventCreate,
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


async def _insert_event(
    session: AsyncSession,
    *,
    payload: EventCreate,
    store: Store,
    product: Product,
) -> datetime | None:
    statement = (
        insert(PosEvent)
        .values(
            event_id=payload.event_id,
            store_id=store.id,
            product_id=product.id,
            event_type=payload.event_type,
            quantity=payload.quantity,
            amount_cents=payload.amount_cents,
            occurred_at=payload.occurred_at,
            original_event_id=_payload_original_event_id(payload),
            source_instance=payload.source_instance,
            metadata_json=payload.metadata,
            note=payload.note,
        )
        .on_conflict_do_nothing(index_elements=[PosEvent.event_id])
        .returning(PosEvent.received_at)
    )
    insert_result = await session.execute(statement)
    return insert_result.scalar_one_or_none()


async def _commit_accepted_event(
    session: AsyncSession,
    *,
    payload: EventCreate,
    store: Store,
    received_at: datetime,
) -> EventIngestionResult:
    store.last_seen_at = received_at
    await session.commit()
    return EventIngestionResult(
        event_id=payload.event_id,
        status="accepted",
        received_at=received_at,
    )


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

    received_at = await _insert_event(
        session,
        payload=payload,
        store=store,
        product=product,
    )
    if received_at is None:
        return await _classify_existing_and_rollback(
            session,
            payload=payload,
            store=store,
            product=product,
        )

    return await _commit_accepted_event(
        session,
        payload=payload,
        store=store,
        received_at=received_at,
    )


async def _lock_original_sale(
    session: AsyncSession,
    original_event_id: UUID,
) -> PosEvent:
    result = await session.execute(
        select(PosEvent)
        .where(PosEvent.event_id == original_event_id)
        .with_for_update()
    )
    original = result.scalar_one_or_none()
    if original is None:
        raise OriginalSaleNotFoundError(str(original_event_id))
    if original.event_type != "SALE" or original.original_event_id is not None:
        raise InvalidOriginalSaleError(str(original_event_id))
    return original


async def _validate_refund_reference(
    session: AsyncSession,
    *,
    original: PosEvent,
    store: Store,
    product: Product,
    payload: RefundEventCreate,
) -> None:
    if original.store_id != store.id:
        raise RefundReferenceMismatchError("refund store must match original sale")
    if original.product_id != product.id:
        raise RefundReferenceMismatchError("refund product must match original sale")

    refunded_quantity, refunded_amount_cents = (
        await session.execute(
            select(
                func.coalesce(func.sum(PosEvent.quantity), 0),
                func.coalesce(func.sum(PosEvent.amount_cents), 0),
            ).where(
                PosEvent.event_type == "REFUND",
                PosEvent.original_event_id == original.event_id,
            )
        )
    ).one()

    if refunded_quantity + payload.quantity > original.quantity:
        raise RefundLimitExceededError("refund exceeds remaining sale quantity")
    if refunded_amount_cents + payload.amount_cents > original.amount_cents:
        raise RefundLimitExceededError("refund exceeds remaining sale amount")


async def ingest_refund_event(
    session: AsyncSession,
    payload: RefundEventCreate,
) -> EventIngestionResult:
    """Persist one REFUND while serializing cumulative limits per original SALE."""
    existing = await session.get(PosEvent, payload.event_id)
    if existing is not None:
        return await _classify_existing_and_rollback(session, payload=payload)

    store = await _find_store(session, payload.store_code)
    product = await _find_product(session, payload.product_sku)
    original = await _lock_original_sale(session, payload.original_event_id)

    # A concurrent identical refund may have committed while this request waited for the
    # original-sale row lock. Re-check the idempotency key before applying cumulative limits.
    existing_after_lock = (
        await session.execute(select(PosEvent).where(PosEvent.event_id == payload.event_id))
    ).scalar_one_or_none()
    if existing_after_lock is not None:
        return await _classify_existing_and_rollback(
            session,
            payload=payload,
            store=store,
            product=product,
        )

    await _validate_refund_reference(
        session,
        original=original,
        store=store,
        product=product,
        payload=payload,
    )

    received_at = await _insert_event(
        session,
        payload=payload,
        store=store,
        product=product,
    )
    if received_at is None:
        return await _classify_existing_and_rollback(
            session,
            payload=payload,
            store=store,
            product=product,
        )

    return await _commit_accepted_event(
        session,
        payload=payload,
        store=store,
        received_at=received_at,
    )
