# POS simulator

Stage 05 replaces the heartbeat-only demo containers with real POS producers. The five
Compose services continuously emit valid `SALE` and `REFUND` events through the same
`POST /api/v1/events` endpoint used by external clients.

## Runtime model

Each simulator owns four independent responsibilities:

1. a heartbeat loop;
2. a stochastic business-event generator;
3. a bounded outbound queue with backpressure;
4. one or more delivery workers with retry-safe HTTP transport.

The generator never changes an event payload after it is created. A retry therefore uses
the same `event_id` and the same logical payload. If the first request committed but its
response was lost, the retry is expected to resolve as the backend's existing
`200 duplicate` path rather than creating another business event.

Retryable conditions are transport failures and HTTP `408`, `425`, `429`, `500`, `502`,
`503`, and `504`. Other HTTP failures are treated as permanent producer/configuration
errors and are logged. The default `MAX_RETRY_ATTEMPTS=0` means retry without a producer-
side attempt limit. Exponential backoff is capped and jittered.

The outbound queue is bounded. When delivery is slower than configured generation,
producers apply backpressure instead of silently dropping newly generated events.

## SALE generation

The simulator uses the same ten SKUs as the deterministic seed. Each product has a stable
simulator-only unit price, and generated totals are integer cents:

```text
amount_cents = unit_price_cents * quantity
```

Quantity is selected from `1..MAX_QUANTITY`.

The product-price catalog is intentionally a producer fixture rather than an application
price table. Case 5 requires POS events to carry their amount; StorePulse does not need a
retail pricing subsystem to rank already-completed sales.

## REFUND generation

A simulator only refunds SALE events that it has already delivered successfully during the
current process lifetime. For every accepted original sale it keeps a small in-memory
ledger of remaining refundable quantity and amount.

Refund capacity is reserved before a REFUND enters the async delivery queue. This prevents
one simulator from locally creating two queued refunds that together exceed its remaining
sale balance. If delivery fails permanently, the reservation is restored. The backend
remains the final authority and independently enforces cumulative refund limits with its
PostgreSQL row lock.

Refund `occurred_at` is never generated before the referenced original sale's
`occurred_at`.

## Deliberate duplicates

After a successful business-event delivery, a configured fraction of events is immediately
replayed with an exact deep copy of the original payload. A correct backend response is
`200 duplicate`. The replay is sent directly by the same delivery worker instead of being
put back into the bounded queue, avoiding a queue-full producer/consumer deadlock.

## Late events

With probability `LATE_EVENT_RATE`, producer `occurred_at` is backdated by a random amount
up to `MAX_LATE_SECONDS`. Database `received_at` is still generated independently by the
backend/PostgreSQL transaction.

This stage proves that late timestamps reach durable storage. Assignment-level proof that
ranking windows use `occurred_at` rather than `received_at` belongs to the analytics stage.

## Instance identity

Each Compose service has a readable `INSTANCE_LABEL`, for example `simulator-madrid`. A `RUN_TAG` separates ordinary demo traffic from verification traffic. At runtime the run tag and container hostname are appended:

```text
simulator-madrid:demo:<container-hostname>
```

This keeps `source_instance` distinct if a simulator service is scaled to multiple
containers.

## Configuration

The checked-in `.env.example` documents every simulator setting. Important controls:

```text
SIMULATOR_RUN_TAG
SIMULATOR_MADRID_EVENTS_PER_SECOND
SIMULATOR_LONDON_EVENTS_PER_SECOND
SIMULATOR_NYC_EVENTS_PER_SECOND
SIMULATOR_TOKYO_EVENTS_PER_SECOND
SIMULATOR_WARSAW_EVENTS_PER_SECOND
SIMULATOR_REFUND_RATE
SIMULATOR_DUPLICATE_RATE
SIMULATOR_LATE_EVENT_RATE
SIMULATOR_MAX_LATE_SECONDS
SIMULATOR_WORKER_COUNT
SIMULATOR_QUEUE_SIZE
SIMULATOR_MAX_RETRY_ATTEMPTS
```

`EVENTS_PER_SECOND` is an average Poisson arrival rate. Each store therefore has an
independently configurable traffic intensity rather than a single global sleep interval.

## Verification strategy

Simulator unit tests cover:

- environment parsing and invalid configuration;
- late-event timestamp generation;
- refund capacity reservation/rollback;
- exact duplicate payload copying;
- retrying a transient failure with the exact same payload/event ID;
- not replaying a non-retryable client error.

The shared `scripts/verify_simulator_smoke.py` harness, invoked by both local `verify.ps1` and GitHub Docker smoke, starts all five POS simulators with deterministic seeds and elevated smoke-test rates. Each verification run uses an isolated run tag and fresh simulator containers so stale database rows or old container logs cannot satisfy the smoke accidentally. Instead of relying on a fixed sleep, the harness polls for up to 35 seconds and requires:

- persisted simulator traffic from exactly five stores;
- at least five SALE rows;
- at least one REFUND row;
- at least one event whose `occurred_at` is materially earlier than `received_at`;
- an observed exact duplicate replay resolved by the backend as `duplicate`;
- exactly one durable database row for the replayed `event_id`.

After the evidence contract passes, the shared harness stops the simulator containers and verifies that they are no longer running. A failed graceful stop gets one explicit `docker compose kill` fallback; if producer termination still cannot be confirmed, database cleanup is skipped rather than racing active writers. The harness then establishes a deterministic backend write barrier by stopping the backend and verifying its stopped state, eliminating any in-flight request path that could still commit verification events. REFUND rows are deleted before SALE parents because `original_event_id` is protected by an `ON DELETE RESTRICT` self-reference. Cleanup runs inside an explicit PostgreSQL transaction with `ON_ERROR_STOP=1`: REFUND rows are deleted first, SALE parents second, and connectivity state is restored before commit. stdout/stderr are captured instead of discarded, so any SQL failure is observable and the transaction rolls back atomically. The harness verifies zero run-tag rows remain, restores the pre-smoke `last_seen_at` and `updated_at` snapshot through typed `json_to_recordset` input, restarts the backend, waits for readiness, then re-verifies that no run-tag rows reappeared and that restored store state still matches the pre-smoke snapshot. Repeated quality-gate runs therefore do not contaminate later ranking demos or depend on timing heuristics for cleanup safety.

## Verified local Stage 05 evidence

The final corrected Windows/Docker verification run completed on 2026-09-09. The complete local quality gate passed repository-wide Ruff, backend mypy, all `47` backend tests, simulator compile, all `9` simulator unit tests, all `16` shared verification-helper tests, frontend typecheck, `2` Vitest tests, frontend production build, backend readiness and the seeded five-store API smoke.

Its isolated producer run tag was `verify-dd56b81aafad`, and the smoke observed:

- durable traffic from exactly five stores;
- `20` SALE rows;
- `19` REFUND rows;
- `39` late rows;
- an exact duplicate replay resolved as `duplicate`;
- exactly `1` durable PostgreSQL row for the replayed `event_id`;
- backend write barrier: PASS;
- simulator verification-data cleanup: PASS;
- backend restart readiness: PASS;
- post-restart run isolation: PASS;
- store connectivity restore: PASS;
- final `Verification completed.`.

These counts are evidence from that isolated verification run, not fixed expectations for normal demo traffic. The previous published Stage 05 candidate had a failing GitHub Actions quality gate; the amended candidate still requires one new green GitHub Actions run before Stage 05 is considered publicly verified.

## Current durability boundary

The producer queue and local refund ledger are intentionally process-local. Network/backend
outages are retried with backpressure, but a hard simulator-process crash can discard events
that were generated but not yet acknowledged. The Case 5 final load proof will measure
accepted producer traffic against durable database events; a durable producer outbox is not
introduced unless the assignment evidence demonstrates that it is necessary.
