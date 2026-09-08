from collections.abc import AsyncIterator

import pytest_asyncio

from app.db import dispose_engine


@pytest_asyncio.fixture(scope="session", autouse=True, loop_scope="session")
async def dispose_database_engine_after_test_session() -> AsyncIterator[None]:
    """Close pooled asyncpg connections before pytest closes the session event loop."""
    yield
    await dispose_engine()
