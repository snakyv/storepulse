from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from random import Random
from typing import Literal
from uuid import UUID, uuid4

from simulator.config import SimulatorConfig


@dataclass(frozen=True, slots=True)
class ProductSpec:
    sku: str
    unit_price_cents: int


PRODUCT_CATALOG: tuple[ProductSpec, ...] = (
    ProductSpec("COFFEE-001", 899),
    ProductSpec("TEA-001", 549),
    ProductSpec("MUG-001", 1299),
    ProductSpec("BOTTLE-001", 1899),
    ProductSpec("NOTE-001", 699),
    ProductSpec("PEN-001", 599),
    ProductSpec("BAG-001", 1499),
    ProductSpec("CABLE-001", 1299),
    ProductSpec("POWER-001", 2499),
    ProductSpec("SNACK-001", 249),
)


@dataclass(slots=True)
class SaleLedgerEntry:
    event_id: UUID
    product_sku: str
    unit_price_cents: int
    occurred_at: datetime
    remaining_quantity: int
    remaining_amount_cents: int


@dataclass(slots=True)
class OutboundEvent:
    payload: dict[str, object]
    kind: Literal["SALE", "REFUND", "DUPLICATE"]
    sale_entry: SaleLedgerEntry | None = None
    refund_original_event_id: UUID | None = None
    reserved_quantity: int = 0
    reserved_amount_cents: int = 0
    allow_deliberate_duplicate: bool = True


class TrafficGenerator:
    def __init__(self, config: SimulatorConfig, rng: Random) -> None:
        self.config = config
        self.rng = rng
        self.sales: dict[UUID, SaleLedgerEntry] = {}

    def _event_time(
        self,
        now: datetime,
        *,
        not_before: datetime | None = None,
    ) -> tuple[datetime, bool]:
        occurred_at = now.astimezone(UTC)
        is_late = self.rng.random() < self.config.late_event_rate
        if is_late:
            seconds = self.rng.randint(1, self.config.max_late_seconds)
            occurred_at -= timedelta(seconds=seconds)
        if not_before is not None and occurred_at < not_before:
            occurred_at = not_before
        return occurred_at, is_late

    def _metadata(self, *, is_late: bool) -> dict[str, object]:
        return {
            "generator": "storepulse-pos-v1",
            "late": is_late,
        }

    def make_sale(self, now: datetime) -> OutboundEvent:
        product = self.rng.choice(PRODUCT_CATALOG)
        quantity = self.rng.randint(1, self.config.max_quantity)
        occurred_at, is_late = self._event_time(now)
        event_id = uuid4()
        amount_cents = product.unit_price_cents * quantity
        sale_entry = SaleLedgerEntry(
            event_id=event_id,
            product_sku=product.sku,
            unit_price_cents=product.unit_price_cents,
            occurred_at=occurred_at,
            remaining_quantity=quantity,
            remaining_amount_cents=amount_cents,
        )
        payload: dict[str, object] = {
            "event_id": str(event_id),
            "store_code": self.config.store_code,
            "product_sku": product.sku,
            "event_type": "SALE",
            "quantity": quantity,
            "amount_cents": amount_cents,
            "occurred_at": occurred_at.isoformat(),
            "source_instance": self.config.instance_label,
            "metadata": self._metadata(is_late=is_late),
        }
        return OutboundEvent(payload=payload, kind="SALE", sale_entry=sale_entry)

    def _refundable_sales(self) -> list[SaleLedgerEntry]:
        return [
            sale
            for sale in self.sales.values()
            if sale.remaining_quantity > 0
            and sale.remaining_amount_cents >= sale.unit_price_cents
        ]

    def make_refund(self, now: datetime) -> OutboundEvent | None:
        candidates = self._refundable_sales()
        if not candidates:
            return None
        original = self.rng.choice(candidates)
        quantity = self.rng.randint(1, original.remaining_quantity)
        amount_cents = original.unit_price_cents * quantity
        occurred_at, is_late = self._event_time(now, not_before=original.occurred_at)
        event_id = uuid4()

        # Reserve the local remaining capacity before the event enters the async queue.
        # This prevents this simulator from producing two refunds that overbook one sale.
        original.remaining_quantity -= quantity
        original.remaining_amount_cents -= amount_cents

        payload: dict[str, object] = {
            "event_id": str(event_id),
            "store_code": self.config.store_code,
            "product_sku": original.product_sku,
            "event_type": "REFUND",
            "quantity": quantity,
            "amount_cents": amount_cents,
            "occurred_at": occurred_at.isoformat(),
            "original_event_id": str(original.event_id),
            "source_instance": self.config.instance_label,
            "metadata": self._metadata(is_late=is_late),
        }
        return OutboundEvent(
            payload=payload,
            kind="REFUND",
            refund_original_event_id=original.event_id,
            reserved_quantity=quantity,
            reserved_amount_cents=amount_cents,
        )

    def make_business_event(self, now: datetime) -> OutboundEvent:
        if self.rng.random() < self.config.refund_rate:
            refund = self.make_refund(now)
            if refund is not None:
                return refund
        return self.make_sale(now)

    def commit_delivery(self, event: OutboundEvent) -> None:
        if event.kind == "SALE" and event.sale_entry is not None:
            self.sales.setdefault(event.sale_entry.event_id, event.sale_entry)

    def rollback_delivery(self, event: OutboundEvent) -> None:
        if event.kind != "REFUND" or event.refund_original_event_id is None:
            return
        original = self.sales.get(event.refund_original_event_id)
        if original is None:
            return
        original.remaining_quantity += event.reserved_quantity
        original.remaining_amount_cents += event.reserved_amount_cents

    def make_duplicate(self, event: OutboundEvent) -> OutboundEvent:
        return OutboundEvent(
            payload=deepcopy(event.payload),
            kind="DUPLICATE",
            allow_deliberate_duplicate=False,
        )
