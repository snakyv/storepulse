from __future__ import annotations

import json
import random
import unittest
from dataclasses import replace

import httpx

from simulator.config import SimulatorConfig
from simulator.transport import PermanentDeliveryError, post_event_with_retry

BASE_CONFIG = SimulatorConfig.from_env(
    {
        "STORE_CODE": "MAD-MADRID",
        "INSTANCE_LABEL": "transport-test",
        "RETRY_INITIAL_SECONDS": "0",
        "RETRY_MAX_SECONDS": "0",
        "RETRY_JITTER_RATIO": "0",
        "MAX_RETRY_ATTEMPTS": "3",
    }
)


class TransportTests(unittest.IsolatedAsyncioTestCase):
    async def test_retry_reuses_exact_payload_and_event_id(self) -> None:
        seen: list[dict[str, object]] = []

        def handler(request: httpx.Request) -> httpx.Response:
            body = json.loads(request.content.decode("utf-8"))
            seen.append(body)
            if len(seen) == 1:
                return httpx.Response(503, json={"detail": "temporary"})
            return httpx.Response(
                201,
                json={
                    "event_id": body["event_id"],
                    "status": "accepted",
                    "received_at": "2026-09-09T00:00:00Z",
                },
            )

        payload: dict[str, object] = {
            "event_id": "11111111-1111-1111-1111-111111111111",
            "event_type": "SALE",
        }
        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport) as client:
            receipt = await post_event_with_retry(
                client,
                endpoint="http://backend/api/v1/events",
                payload=payload,
                config=BASE_CONFIG,
                rng=random.Random(1),
            )

        self.assertEqual(receipt.status, "accepted")
        self.assertEqual(receipt.attempts, 2)
        self.assertEqual(seen, [payload, payload])

    async def test_non_retryable_error_is_not_replayed(self) -> None:
        requests = 0

        def handler(_: httpx.Request) -> httpx.Response:
            nonlocal requests
            requests += 1
            return httpx.Response(422, json={"detail": "bad payload"})

        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport) as client:
            with self.assertRaises(PermanentDeliveryError):
                await post_event_with_retry(
                    client,
                    endpoint="http://backend/api/v1/events",
                    payload={"event_id": "x"},
                    config=replace(BASE_CONFIG, max_retry_attempts=1),
                    rng=random.Random(1),
                )

        self.assertEqual(requests, 1)


if __name__ == "__main__":
    unittest.main()
