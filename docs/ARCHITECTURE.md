# Architecture

## Current components

```text
Five POS simulator containers (heartbeat-only until Stage 05)
          |
          | HTTP heartbeat
          v
      FastAPI API <------ POST /api/v1/events from POS clients/tests
       |       |
       |       +---- WebSocket invalidation ----> Vue clients
       |
       +---- PostgreSQL
             stores
             products
             pos_events
```

PostgreSQL is authoritative. WebSocket messages contain invalidation information only; clients refetch authoritative state through REST.

## Why this shape

The assignment requires separate backend/frontend, relational persistence, multiple simultaneous clients and realtime updates. A single FastAPI process plus PostgreSQL is sufficient for the assessment scale. Redis/Kafka are intentionally absent until horizontal scaling creates a real need.

## Durable schema

- `stores` — identity, timezone, daily target, responsible person, heartbeat timestamp.
- `products` — stable product catalogue.
- `pos_events` — append-only SALE/REFUND events with producer event time and server reception time.

Money is represented in integer minor units (`*_cents`). Persisted event timestamps use timezone-aware PostgreSQL timestamps.

Migration `20260908_0002_refund_invariants.py` adds database checks requiring SALE rows to have no original reference, REFUND rows to have one, and prohibiting self-reference.

## Event identity and idempotency

`event_id` is the event identity and PostgreSQL primary key. Both SALE and REFUND ingestion use PostgreSQL-specific `INSERT ... ON CONFLICT DO NOTHING` as the final concurrency authority.

```text
validate request
    |
    +-- existing event_id? -- yes --> compare immutable logical payload
    |                                  | same      -> 200 duplicate
    |                                  + different -> 409 conflict
    |
    +-- no --> event-specific validation
               |
               +-- INSERT ... ON CONFLICT DO NOTHING RETURNING received_at
                      | inserted -> update store.last_seen_at -> COMMIT -> 201
                      |
                      + conflict -> re-read winner -> duplicate / 409
```

This avoids treating an application `SELECT-if-absent` check as authoritative. Concurrent identical requests can create only one primary-key row.

## Refund concurrency model

Refunds add a second concurrency invariant: cumulative refund quantity and amount must never exceed the original sale.

The service locks the referenced SALE row with `SELECT ... FOR UPDATE` before reading cumulative refunds. Requests refunding the same sale therefore serialize their limit decisions, while refunds for unrelated sales remain independent.

```text
resolve store/product
      |
lock original SALE row FOR UPDATE
      |
re-check refund event_id after any lock wait
      |
validate original type + same store/product
      |
sum committed refunds for original SALE
      |
check remaining quantity and amount independently
      |
insert REFUND with event_id ON CONFLICT protection
      |
commit
```

The post-lock event-ID re-check is essential: an identical retry may have been waiting while the first refund committed. Re-checking turns it into `200 duplicate` before cumulative limits are applied a second time.

Cross-row rules such as original-event type, same store/product and cumulative limits remain transactional service invariants because row CHECK constraints cannot safely express them.

See `docs/REFUNDS.md` for the full contract.

## Event time

The producer's timezone-aware `occurred_at` is stored independently from PostgreSQL-assigned `received_at` for both sales and refunds. Future analytics will filter/aggregate on `occurred_at`, allowing late delivery without moving the event into the reception-time window.

## Startup order

```text
postgres healthy
   -> alembic migrate
      -> deterministic seed
         -> backend healthy
            -> frontend / optional demo simulators
```

## Realtime invalidation

A heartbeat commits `last_seen_at` and then broadcasts `stores.changed`.

A newly accepted SALE or REFUND commits the event plus updated store connectivity and then broadcasts `events.changed`. Exact duplicates and rejected requests do not broadcast a business-state change.

The Vue client treats these as invalidations and refetches REST state. This keeps PostgreSQL/REST authoritative and avoids maintaining a second ranking state inside WebSocket messages.

## Async engine lifecycle

The backend owns one lazily created pooled SQLAlchemy `AsyncEngine` per process. FastAPI lifespan shutdown disposes it explicitly. The pytest suite mirrors that model with a session-scoped asyncio loop and explicit engine disposal before the loop closes.

## Deliberately deferred

The current architecture does not yet include:

- POS sale/refund generation from simulators;
- ranking queries and materialized aggregates;
- persisted dashboard settings;
- offline incident/outbox worker;
- local-noon alert evaluation.

Those are added only when their feature stages require them.
