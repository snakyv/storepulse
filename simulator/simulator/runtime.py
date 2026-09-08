from __future__ import annotations

import asyncio
import logging
import random
import socket
from dataclasses import dataclass, replace
from datetime import UTC, datetime

import httpx

from simulator.config import SimulatorConfig
from simulator.domain import OutboundEvent, TrafficGenerator
from simulator.transport import (
    PermanentDeliveryError,
    RetryExhaustedError,
    post_event_with_retry,
)

logger = logging.getLogger("storepulse.simulator")


@dataclass(slots=True)
class SimulatorStats:
    generated_sales: int = 0
    generated_refunds: int = 0
    delivered_accepted: int = 0
    delivered_duplicate: int = 0
    deliberate_duplicates: int = 0
    duplicate_replay_failures: int = 0
    retry_attempts: int = 0
    permanent_failures: int = 0


async def _heartbeat_loop(
    client: httpx.AsyncClient,
    config: SimulatorConfig,
) -> None:
    endpoint = f"{config.backend_url}/api/v1/stores/{config.store_code}/heartbeat"
    while True:
        try:
            response = await client.post(endpoint)
            response.raise_for_status()
            logger.debug("heartbeat accepted store=%s", config.store_code)
        except httpx.HTTPError as exc:
            logger.warning("heartbeat failed store=%s error=%s", config.store_code, exc)
        await asyncio.sleep(config.heartbeat_interval)


async def _traffic_loop(
    queue: asyncio.Queue[OutboundEvent],
    generator: TrafficGenerator,
    stats: SimulatorStats,
) -> None:
    while True:
        delay = generator.rng.expovariate(generator.config.events_per_second)
        await asyncio.sleep(delay)
        event = generator.make_business_event(datetime.now(UTC))
        if event.kind == "REFUND":
            stats.generated_refunds += 1
        else:
            stats.generated_sales += 1
        await queue.put(event)


async def _delivery_worker(
    worker_id: int,
    queue: asyncio.Queue[OutboundEvent],
    client: httpx.AsyncClient,
    generator: TrafficGenerator,
    config: SimulatorConfig,
    stats: SimulatorStats,
) -> None:
    endpoint = f"{config.backend_url}/api/v1/events"
    worker_rng = random.Random(config.random_seed + 10_000 + worker_id)
    while True:
        event = await queue.get()
        try:
            receipt = await post_event_with_retry(
                client,
                endpoint=endpoint,
                payload=event.payload,
                config=config,
                rng=worker_rng,
            )
        except (PermanentDeliveryError, RetryExhaustedError) as exc:
            generator.rollback_delivery(event)
            stats.permanent_failures += 1
            logger.error(
                "event delivery failed store=%s kind=%s event_id=%s error=%s",
                config.store_code,
                event.kind,
                event.payload.get("event_id"),
                exc,
            )
        else:
            stats.retry_attempts += max(0, receipt.attempts - 1)
            if receipt.status == "accepted":
                stats.delivered_accepted += 1
            else:
                stats.delivered_duplicate += 1
            generator.commit_delivery(event)
            logger.info(
                "event delivered store=%s kind=%s status=%s attempts=%s event_id=%s",
                config.store_code,
                event.kind,
                receipt.status,
                receipt.attempts,
                event.payload.get("event_id"),
            )
            if (
                event.allow_deliberate_duplicate
                and worker_rng.random() < config.duplicate_rate
            ):
                replay = generator.make_duplicate(event)
                try:
                    replay_receipt = await post_event_with_retry(
                        client,
                        endpoint=endpoint,
                        payload=replay.payload,
                        config=config,
                        rng=worker_rng,
                    )
                except (PermanentDeliveryError, RetryExhaustedError) as exc:
                    stats.duplicate_replay_failures += 1
                    logger.error(
                        "duplicate replay failed store=%s event_id=%s error=%s",
                        config.store_code,
                        replay.payload.get("event_id"),
                        exc,
                    )
                else:
                    stats.retry_attempts += max(0, replay_receipt.attempts - 1)
                    stats.deliberate_duplicates += 1
                    if replay_receipt.status == "duplicate":
                        stats.delivered_duplicate += 1
                    else:
                        stats.delivered_accepted += 1
                        logger.warning(
                            "duplicate replay unexpectedly accepted event_id=%s",
                            replay.payload.get("event_id"),
                        )
                    logger.info(
                        "event delivered store=%s kind=DUPLICATE status=%s "
                        "attempts=%s event_id=%s",
                        config.store_code,
                        replay_receipt.status,
                        replay_receipt.attempts,
                        replay.payload.get("event_id"),
                    )
        finally:
            queue.task_done()


async def _stats_loop(
    queue: asyncio.Queue[OutboundEvent],
    config: SimulatorConfig,
    stats: SimulatorStats,
) -> None:
    while True:
        await asyncio.sleep(config.stats_interval_seconds)
        logger.info(
            "stats store=%s sales=%s refunds=%s accepted=%s duplicates=%s "
            "duplicate_replays=%s replay_failures=%s retries=%s failures=%s queue=%s",
            config.store_code,
            stats.generated_sales,
            stats.generated_refunds,
            stats.delivered_accepted,
            stats.delivered_duplicate,
            stats.deliberate_duplicates,
            stats.duplicate_replay_failures,
            stats.retry_attempts,
            stats.permanent_failures,
            queue.qsize(),
        )


async def run(config: SimulatorConfig) -> None:
    hostname = socket.gethostname()
    effective_label = f"{config.instance_label}:{config.run_tag}:{hostname}"
    config = replace(config, instance_label=effective_label)
    generator = TrafficGenerator(config, random.Random(config.random_seed))
    queue: asyncio.Queue[OutboundEvent] = asyncio.Queue(maxsize=config.queue_size)
    stats = SimulatorStats()
    limits = httpx.Limits(
        max_connections=config.worker_count + 2,
        max_keepalive_connections=config.worker_count + 2,
    )
    timeout = httpx.Timeout(config.request_timeout_seconds)

    logger.info(
        "starting POS simulator store=%s instance=%s eps=%.3f refund=%.2f "
        "duplicate=%.2f late=%.2f workers=%s",
        config.store_code,
        config.instance_label,
        config.events_per_second,
        config.refund_rate,
        config.duplicate_rate,
        config.late_event_rate,
        config.worker_count,
    )

    async with httpx.AsyncClient(timeout=timeout, limits=limits) as client:
        async with asyncio.TaskGroup() as tasks:
            tasks.create_task(_heartbeat_loop(client, config))
            tasks.create_task(_traffic_loop(queue, generator, stats))
            tasks.create_task(_stats_loop(queue, config, stats))
            for worker_id in range(config.worker_count):
                tasks.create_task(
                    _delivery_worker(
                        worker_id,
                        queue,
                        client,
                        generator,
                        config,
                        stats,
                    )
                )
