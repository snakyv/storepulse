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
- `pos_events` — append-only SALE/REFUND-shaped event table. Stage 03 exposes validated SALE ingestion; refund validation is intentionally deferred to Stage 04.

Money is represented in integer minor units (`*_cents`). Persisted event timestamps use timezone-aware PostgreSQL timestamps.

## SALE ingestion and idempotency

`event_id` is the event identity and the PostgreSQL primary key. The API uses PostgreSQL-specific `INSERT ... ON CONFLICT DO NOTHING` as the concurrency authority.

```text
validate request
    |
    +-- existing event_id? -- yes --> compare immutable payload
    |                                  | same      -> 200 duplicate
    |                                  + different -> 409 conflict
    |
    +-- no --> resolve store + product
               |
               +-- INSERT ... ON CONFLICT DO NOTHING RETURNING received_at
                      | inserted -> update store.last_seen_at -> COMMIT -> 201
                      |
                      + conflict -> re-read winner -> duplicate / 409
```

This avoids the unsafe `SELECT-if-absent` followed by unconditional `INSERT` pattern. Concurrent identical requests can create only one primary-key row; concurrent conflicting requests resolve to one accepted row and one conflict.

The producer's timezone-aware `occurred_at` is stored independently from PostgreSQL-assigned `received_at`. Analytics will use `occurred_at`, so late delivery does not silently move a sale into the reception-time window.

Full request/response semantics are documented in `docs/EVENT_INGESTION.md`.

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

A newly accepted sale commits the event plus the updated store `last_seen_at` and then broadcasts `events.changed`. The current Vue foundation treats either invalidation as a reason to refetch store state. Later ranking views will use the same REST-as-authority pattern.

Duplicate retries and rejected conflicts do not emit a business-state invalidation because they do not change the event table.

## Async database lifecycle

The backend lazily creates one pooled SQLAlchemy `AsyncEngine` per application process. Uvicorn serves the application on one asyncio event loop, and FastAPI lifespan shutdown explicitly disposes the engine pool. The pytest suite mirrors that process model with a session-scoped asyncio loop and disposes the pool before pytest closes the loop. This avoids sharing pooled asyncpg connections across unrelated event loops while preserving normal pooling in the application.
