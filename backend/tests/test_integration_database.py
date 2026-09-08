import pytest
from sqlalchemy import func, select, text

from app.db import get_session_factory
from app.models import Product, Store


@pytest.mark.integration
@pytest.mark.asyncio
async def test_migrations_and_seed_are_available() -> None:
    async with get_session_factory()() as session:
        assert (await session.execute(text("SELECT 1"))).scalar_one() == 1
        store_count = (
            await session.execute(select(func.count()).select_from(Store))
        ).scalar_one()
        product_count = (
            await session.execute(select(func.count()).select_from(Product))
        ).scalar_one()

    assert store_count == 5
    assert product_count == 10
