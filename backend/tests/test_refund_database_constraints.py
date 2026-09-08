from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.db import get_session_factory
from app.models import PosEvent, Product, Store


@pytest.mark.integration
@pytest.mark.asyncio
async def test_database_rejects_refund_without_original_reference() -> None:
    async with get_session_factory()() as session:
        store = (
            await session.execute(select(Store).where(Store.code == "MAD-MADRID"))
        ).scalar_one()
        product = (
            await session.execute(select(Product).where(Product.sku == "COFFEE-001"))
        ).scalar_one()
        event = PosEvent(
            event_id=uuid4(),
            store_id=store.id,
            product_id=product.id,
            event_type="REFUND",
            quantity=1,
            amount_cents=100,
            occurred_at=datetime.now(UTC),
            original_event_id=None,
            source_instance="pytest:refund-db-constraint",
        )
        session.add(event)

        with pytest.raises(IntegrityError):
            await session.flush()
        await session.rollback()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_database_rejects_self_referencing_refund() -> None:
    event_id = uuid4()
    async with get_session_factory()() as session:
        store = (
            await session.execute(select(Store).where(Store.code == "MAD-MADRID"))
        ).scalar_one()
        product = (
            await session.execute(select(Product).where(Product.sku == "COFFEE-001"))
        ).scalar_one()
        event = PosEvent(
            event_id=event_id,
            store_id=store.id,
            product_id=product.id,
            event_type="REFUND",
            quantity=1,
            amount_cents=100,
            occurred_at=datetime.now(UTC),
            original_event_id=event_id,
            source_instance="pytest:refund-db-constraint",
        )
        session.add(event)

        with pytest.raises(IntegrityError):
            await session.flush()
        await session.rollback()
