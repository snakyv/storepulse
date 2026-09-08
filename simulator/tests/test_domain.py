from __future__ import annotations

import random
import unittest
from dataclasses import replace
from datetime import UTC, datetime, timedelta

from simulator.config import SimulatorConfig
from simulator.domain import TrafficGenerator

BASE_CONFIG = SimulatorConfig.from_env(
    {
        "STORE_CODE": "MAD-MADRID",
        "INSTANCE_LABEL": "simulator-test",
        "REFUND_RATE": "0",
        "DUPLICATE_RATE": "0",
        "LATE_EVENT_RATE": "0",
        "RANDOM_SEED": "7",
    }
)


class TrafficGeneratorTests(unittest.TestCase):
    def test_late_sale_preserves_event_time_before_delivery_time(self) -> None:
        config = replace(BASE_CONFIG, late_event_rate=1.0, max_late_seconds=60)
        generator = TrafficGenerator(config, random.Random(3))
        now = datetime(2026, 9, 9, 12, 0, tzinfo=UTC)

        event = generator.make_sale(now)
        occurred_at = datetime.fromisoformat(str(event.payload["occurred_at"]))

        self.assertLess(occurred_at, now)
        self.assertGreaterEqual(occurred_at, now - timedelta(seconds=60))
        self.assertEqual(
            event.payload["metadata"],
            {"generator": "storepulse-pos-v1", "late": True},
        )

    def test_refund_reserves_capacity_and_rollback_restores_it(self) -> None:
        config = replace(BASE_CONFIG, refund_rate=1.0)
        generator = TrafficGenerator(config, random.Random(5))
        now = datetime(2026, 9, 9, 12, 0, tzinfo=UTC)
        sale = generator.make_sale(now)
        generator.commit_delivery(sale)
        original = sale.sale_entry
        assert original is not None
        quantity_before = original.remaining_quantity
        amount_before = original.remaining_amount_cents

        refund = generator.make_refund(now + timedelta(minutes=5))
        assert refund is not None

        self.assertLess(original.remaining_quantity, quantity_before)
        self.assertLess(original.remaining_amount_cents, amount_before)
        self.assertEqual(refund.payload["original_event_id"], str(original.event_id))

        generator.rollback_delivery(refund)
        self.assertEqual(original.remaining_quantity, quantity_before)
        self.assertEqual(original.remaining_amount_cents, amount_before)

    def test_duplicate_replay_is_payload_identical_and_has_no_state_effect(self) -> None:
        generator = TrafficGenerator(BASE_CONFIG, random.Random(11))
        now = datetime(2026, 9, 9, 12, 0, tzinfo=UTC)
        sale = generator.make_sale(now)
        replay = generator.make_duplicate(sale)

        self.assertEqual(replay.payload, sale.payload)
        self.assertIsNot(replay.payload, sale.payload)
        self.assertEqual(replay.kind, "DUPLICATE")
        self.assertFalse(replay.allow_deliberate_duplicate)


if __name__ == "__main__":
    unittest.main()
