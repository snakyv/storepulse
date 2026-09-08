# Architecture — foundation checkpoint

## Current components

```text
Five POS heartbeat simulators
          |
          | HTTP POST /heartbeat
          v
      FastAPI API
       |       |
       |       +---- WebSocket invalidation ----> Vue clients
       |
       +---- PostgreSQL
```

PostgreSQL is authoritative. WebSocket messages contain invalidation information only; clients refetch store state from REST.

## Why this shape

The assignment requires separate backend/frontend, relational persistence, multiple simultaneous clients and realtime updates. A single FastAPI process plus PostgreSQL is sufficient for the assessment scale. Redis/Kafka are intentionally absent until horizontal scaling creates a real need.

## Current durable schema

- `stores` — identity, timezone, daily target, responsible person, heartbeat timestamp.
- `products` — stable product catalogue.
- `pos_events` — append-only event-shaped table prepared for SALE/REFUND ingestion. The API for inserting events is intentionally not implemented in this checkpoint.

Money is represented in integer minor units (`*_cents`). Persisted event timestamps use timezone-aware PostgreSQL timestamps.

## Startup order

```text
postgres healthy
   -> alembic migrate
      -> deterministic seed
         -> backend healthy
            -> frontend / optional demo simulators
```

## Realtime foundation

A simulator heartbeat commits `last_seen_at` first. Only after commit does the API broadcast `stores.changed`. Every connected Vue client debounces that signal and fetches authoritative store state through REST.

This is intentionally the same pattern planned for later sales/ranking invalidation.


## Async database lifecycle

The backend lazily creates one pooled SQLAlchemy `AsyncEngine` per application process. Uvicorn serves the application on one asyncio event loop, and FastAPI lifespan shutdown explicitly disposes the engine pool. The pytest suite mirrors that process model with a session-scoped asyncio loop and disposes the pool before pytest closes the loop. This avoids sharing pooled asyncpg connections across unrelated event loops while preserving normal pooling in the application.
