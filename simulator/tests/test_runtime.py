from __future__ import annotations

import asyncio
import json
import random
import unittest
from contextlib import suppress
from dataclasses import replace
from datetime import UTC, datetime

import httpx

from simulator.config import SimulatorConfig
from simulator.domain import OutboundEvent, TrafficGenerator
from simulator.runtime import SimulatorStats, _delivery_worker

BASE_CONFIG = SimulatorConfig.from_env(
    {
        "STORE_CODE": "MAD-MADRID",
        "INSTANCE_LABEL": "runtime-test",
        "RUN_TAG": "unit",
        "DUPLICATE_RATE": "1",
        "RETRY_INITIAL_SECONDS": "0",
        "RETRY_MAX_SECONDS": "0",
        "RETRY_JITTER_RATIO": "0",
        "MAX_RETRY_ATTEMPTS": "2",
    }
)


class DeliveryWorkerTests(unittest.IsolatedAsyncioTestCase):
    async def test_successful_event_is_replayed_exactly_once_as_duplicate(self) -> None:
        seen: list[dict[str, object]] = []

        def handler(request: httpx.Request) -> httpx.Response:
            body = json.loads(request.content.decode("utf-8"))
            seen.append(body)
            status = "accepted" if len(seen) == 1 else "duplicate"
            http_status = 201 if len(seen) == 1 else 200
            return httpx.Response(
                http_status,
                json={
                    "event_id": body["event_id"],
                    "status": status,
                    "received_at": "2026-09-09T00:00:00Z",
                },
            )

        generator = TrafficGenerator(BASE_CONFIG, random.Random(9))
        event = generator.make_sale(datetime(2026, 9, 9, 12, 0, tzinfo=UTC))
        queue: asyncio.Queue[OutboundEvent] = asyncio.Queue()
        await queue.put(event)
        stats = SimulatorStats()

        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport) as client:
            worker = asyncio.create_task(
                _delivery_worker(
                    0,
                    queue,
                    client,
                    generator,
                    replace(BASE_CONFIG, duplicate_rate=1.0),
                    stats,
                )
            )
            await asyncio.wait_for(queue.join(), timeout=1.0)
            worker.cancel()
            with suppress(asyncio.CancelledError):
                await worker

        self.assertEqual(len(seen), 2)
        self.assertEqual(seen[0], seen[1])
        self.assertEqual(stats.delivered_accepted, 1)
        self.assertEqual(stats.delivered_duplicate, 1)
        self.assertEqual(stats.deliberate_duplicates, 1)
        self.assertEqual(stats.duplicate_replay_failures, 0)
        sale_entry = event.sale_entry
        assert sale_entry is not None
        self.assertIn(sale_entry.event_id, generator.sales)


if __name__ == "__main__":
    unittest.main()
