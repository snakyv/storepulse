# Architecture

## System shape

StorePulse remains a deliberately small monorepo:

```text
five POS simulators ---- HTTP heartbeat / SALE / REFUND ----> FastAPI
                                                              |
Vue clients <---- REST + WebSocket invalidation --------------+
                                                              |
                                                              v
                                                         PostgreSQL
```

PostgreSQL is the source of truth. The browser never treats WebSocket payloads as authoritative state; a socket message invalidates local data and the client refetches REST state.

## Backend event authority

`POST /api/v1/events` accepts immutable SALE/REFUND events.

Event identity is the PostgreSQL `pos_events.event_id` primary key. SALE ingestion uses PostgreSQL conflict handling rather than a process-local deduplication cache. Exact retries therefore converge on one durable row even when requests are concurrent.

REFUND events reference an original SALE. Cumulative refund quantity and amount are protected by `SELECT ... FOR UPDATE` on the original-sale row. This serializes refund-limit decisions across concurrent requests and future application processes.

## Producer architecture

Stage 05 gives every simulator four independent responsibilities:

```text
heartbeat loop

traffic clock
   |
   v
SALE / REFUND generator
   |
   v
bounded asyncio.Queue  <---- backpressure when delivery is slower
   |
   +----------> delivery worker 1 ----+
   |                                  |
   +----------> delivery worker N ----+---- HTTP /api/v1/events
                                      |
                                      +---- exact duplicate replay
```

The traffic clock uses an exponential inter-arrival distribution with configured mean events per second. Each store has its own Compose environment control.

### Immutable retry identity

The simulator creates a complete JSON payload once. Retry logic receives that dictionary and resends it unchanged:

```text
attempt 1: event_id=A, payload=P
network/5xx ambiguity
attempt 2: event_id=A, payload=P
```

It never does this:

```text
attempt 2: event_id=B
```

This is essential because a timeout can occur after the backend has committed. Reusing `(A, P)` lets the backend answer `duplicate`; generating `(B, P)` would create a double sale.

Retryable conditions are transport failures plus HTTP 408/425/429/5xx transient statuses. Backoff is exponential, capped and jittered. Non-retryable client errors are surfaced in logs instead of retried forever.

### Queue and backpressure

The outbound event queue is bounded. When all delivery workers are slower than generation, `queue.put()` blocks the traffic loop. The producer therefore slows down rather than silently dropping generated events or allowing unbounded memory growth.

Deliberate duplicates are not reinserted into that queue. A worker replays the exact payload directly after original success, preventing a bounded-queue deadlock in which every consumer could block while trying to enqueue more work.

### Refund producer state

The simulator only knows about sales that it has successfully delivered. It keeps a small process-local ledger containing original event ID, SKU, unit price, original time and remaining refundable amount/quantity.

When generating a refund, remaining local capacity is reserved before the event is queued. If delivery ends in a permanent producer-side failure, that reservation is restored. This prevents local overbooking but does not replace backend validation.

The simulator ledger is intentionally not durable. PostgreSQL remains the correctness authority.

### Late events

For configured events, producer `occurred_at` is shifted into the past up to `MAX_LATE_SECONDS`; backend/database `received_at` remains independent. Refund event time is clamped so it is never earlier than its original sale.

Stage 05 proves generation/persistence of late timestamps. Ranking assignment by `occurred_at` is verified in the analytics stage.

## Five simulator instances

Compose defines:

```text
simulator-madrid
simulator-london
simulator-new-york
simulator-tokyo
simulator-warsaw
```

Each service has its own store code, deterministic random seed and events-per-second setting. A readable service label, run tag and container hostname are stored in `source_instance`, so scaling a service does not collapse multiple producers into one source identity.

## Realtime pattern

Accepted events trigger an `events.changed` WebSocket invalidation. Exact duplicates do not broadcast false business changes. The Vue client coalesces bursty invalidations into bounded REST refreshes and never runs overlapping store refresh requests; ranking-specific refetch behavior is added in the analytics/UI stages.

## Time and money

- money remains integer cents;
- event instants are timezone-aware;
- producer `occurred_at` is preserved;
- PostgreSQL assigns `received_at`;
- store business timezones are IANA identifiers;
- future `today` windows must convert each store's local midnight to UTC rather than assuming UTC midnight.

## Verification architecture

Local verification now includes:

```text
backend lint/type/tests
simulator compile + unit tests
frontend type/tests/build
real backend API smoke
five real POS simulator containers
PostgreSQL durable traffic inspection
verified producer stop + backend write barrier + transactional simulator cleanup
```

GitHub Actions invokes the same repository-wide Ruff runner and the same five-container Python smoke/cleanup harness as local verification, eliminating shell-specific target and lifecycle drift.

See `EVENT_INGESTION.md`, `REFUNDS.md`, `SIMULATOR.md` and `REQUIREMENTS_TRACEABILITY.md` for feature-level contracts and current proof status.
