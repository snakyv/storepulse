import asyncio
import uuid

from sqlalchemy.dialects.postgresql import insert

from app.db import get_session_factory
from app.models import Product, Store

NAMESPACE = uuid.UUID("8e0785c2-6900-4d7a-a7cb-19cc53521ed7")

STORES = [
    (
        "MAD-MADRID",
        "Madrid Central",
        "Europe/Madrid",
        180_000,
        "Ana Ruiz",
        "madrid.manager@example.test",
    ),
    (
        "MAD-LONDON",
        "London West",
        "Europe/London",
        220_000,
        "James Cole",
        "london.manager@example.test",
    ),
    (
        "MAD-NYC",
        "New York Midtown",
        "America/New_York",
        300_000,
        "Taylor Reed",
        "nyc.manager@example.test",
    ),
    (
        "MAD-TOKYO",
        "Tokyo Shibuya",
        "Asia/Tokyo",
        260_000,
        "Aiko Mori",
        "tokyo.manager@example.test",
    ),
    (
        "MAD-WARSAW",
        "Warsaw Centrum",
        "Europe/Warsaw",
        160_000,
        "Marta Nowak",
        "warsaw.manager@example.test",
    ),
]

PRODUCTS = [
    ("COFFEE-001", "Coffee Beans 500g", "Grocery"),
    ("TEA-001", "Green Tea", "Grocery"),
    ("MUG-001", "Ceramic Mug", "Home"),
    ("BOTTLE-001", "Reusable Bottle", "Home"),
    ("NOTE-001", "Notebook", "Stationery"),
    ("PEN-001", "Gel Pen Set", "Stationery"),
    ("BAG-001", "Canvas Tote", "Accessories"),
    ("CABLE-001", "USB-C Cable", "Electronics"),
    ("POWER-001", "Power Adapter", "Electronics"),
    ("SNACK-001", "Granola Bar", "Grocery"),
]


def stable_id(kind: str, value: str) -> uuid.UUID:
    return uuid.uuid5(NAMESPACE, f"{kind}:{value}")


async def seed() -> None:
    async with get_session_factory()() as session:
        for code, name, tz, target, responsible_name, responsible_email in STORES:
            stmt = insert(Store).values(
                id=stable_id("store", code),
                code=code,
                name=name,
                timezone=tz,
                daily_target_cents=target,
                responsible_name=responsible_name,
                responsible_email=responsible_email,
                is_active=True,
            )
            await session.execute(stmt.on_conflict_do_nothing(index_elements=[Store.code]))

        for sku, name, category in PRODUCTS:
            stmt = insert(Product).values(
                id=stable_id("product", sku),
                sku=sku,
                name=name,
                category=category,
            )
            await session.execute(stmt.on_conflict_do_nothing(index_elements=[Product.sku]))

        await session.commit()


if __name__ == "__main__":
    asyncio.run(seed())
