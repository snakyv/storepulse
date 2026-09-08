from __future__ import annotations

import asyncio
from dataclasses import dataclass
from random import Random
from typing import Literal

import httpx

from simulator.config import SimulatorConfig

RETRYABLE_STATUS_CODES = {408, 425, 429, 500, 502, 503, 504}
SUCCESS_STATUS_CODES = {200, 201}


class PermanentDeliveryError(RuntimeError):
    pass


class RetryExhaustedError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class DeliveryReceipt:
    status: Literal["accepted", "duplicate"]
    http_status: int
    attempts: int


def _retry_delay(config: SimulatorConfig, attempt: int, rng: Random) -> float:
    base = min(
        config.retry_initial_seconds * (2 ** max(0, attempt - 1)),
        config.retry_max_seconds,
    )
    if base == 0 or config.retry_jitter_ratio == 0:
        return base
    jitter = base * config.retry_jitter_ratio
    return max(0.0, rng.uniform(base - jitter, base + jitter))


async def post_event_with_retry(
    client: httpx.AsyncClient,
    *,
    endpoint: str,
    payload: dict[str, object],
    config: SimulatorConfig,
    rng: Random,
) -> DeliveryReceipt:
    attempt = 0
    while True:
        attempt += 1
        try:
            response = await client.post(endpoint, json=payload)
        except httpx.TransportError as exc:
            retry_reason = f"transport error: {exc}"
        else:
            if response.status_code in SUCCESS_STATUS_CODES:
                try:
                    body = response.json()
                    status = body["status"]
                except (ValueError, KeyError, TypeError) as exc:
                    retry_reason = f"invalid success response: {exc}"
                else:
                    if status not in {"accepted", "duplicate"}:
                        retry_reason = f"invalid success status: {status!r}"
                    else:
                        return DeliveryReceipt(
                            status=status,
                            http_status=response.status_code,
                            attempts=attempt,
                        )
            elif response.status_code in RETRYABLE_STATUS_CODES:
                retry_reason = f"retryable HTTP {response.status_code}"
            else:
                detail = response.text[:500]
                raise PermanentDeliveryError(
                    f"non-retryable HTTP {response.status_code}: {detail}"
                )

        if config.max_retry_attempts and attempt >= config.max_retry_attempts:
            raise RetryExhaustedError(
                f"delivery failed after {attempt} attempts: {retry_reason}"
            )
        await asyncio.sleep(_retry_delay(config, attempt, rng))
