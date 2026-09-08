# POS event ingestion contract — Stages 03–04

`POST /api/v1/events` accepts a discriminated event body selected by `event_type`:

- `SALE` — introduced in Stage 03;
- `REFUND` — introduced in Stage 04 with original-sale and cumulative-limit validation.

Both event types share the same database-authoritative `event_id` idempotency contract. Refund-specific rules are documented in `docs/REFUNDS.md`.

## SALE request

```json
{
  "event_id": "2bc00f92-ec88-4c3c-9302-7d8754540706",
  "store_code": "MAD-MADRID",
  "product_sku": "COFFEE-001",
  "event_type": "SALE",
  "quantity": 2,
  "amount_cents": 1598,
  "occurred_at": "2026-09-08T18:20:00Z",
  "source_instance": "simulator-madrid-1",
  "metadata": {
    "terminal": "POS-01"
  },
  "note": null
}
```

A refund has the same common fields plus `event_type: "REFUND"` and a required `original_event_id`.

## Common validation

- `event_id` is a producer-supplied UUID and the idempotency identity.
- `quantity` and `amount_cents` are strict positive integers.
- `occurred_at` must include timezone information.
- `store_code`, `product_sku` and `source_instance` must be non-empty and fit persisted field limits.
- additional request fields are rejected instead of ignored.
- money remains integer minor units; floating-point currency values are not accepted.

## Idempotency semantics

The PostgreSQL primary key on `pos_events.event_id` is authoritative. Ingestion uses PostgreSQL `INSERT ... ON CONFLICT DO NOTHING`, not an application-only check-then-insert race.

For a previously unseen ID:

```text
POST /api/v1/events
→ PostgreSQL INSERT ... ON CONFLICT DO NOTHING
→ one row committed
→ 201 accepted
```

For an exact replay:

```text
first request  → 201 accepted
retry          → 200 duplicate
row count      → still 1
received_at    → original value is returned
```

For the same ID with any different logical payload field:

```text
→ 409 Conflict
→ original row remains unchanged
```

Duplicate comparison includes store, product, event type, quantity, amount, `occurred_at`, original-event reference where applicable, source instance, metadata and note. `received_at` is server-assigned and is not part of producer equivalence.

## Event time

`occurred_at` is stored as the timezone-aware business-event instant supplied by the producer. `received_at` is assigned independently by PostgreSQL.

A late event is therefore represented as:

```text
occurred_at < received_at
```

Both SALE and REFUND preserve this distinction. Ranking windows will use `occurred_at` in the analytics stage.

## Realtime invalidation

A newly accepted event updates store connectivity and commits before broadcasting `events.changed`. WebSocket messages remain invalidation-only: clients refetch authoritative REST state. Duplicate/conflicting/rejected requests do not broadcast a business-state change because they do not create a new event row.

## Test isolation

Integration tests use reserved `pytest:*` source prefixes, remove their own event rows and restore store `last_seen_at`. Refund cleanup deletes dependent refund rows before their test sales, respecting the self-referential foreign key. Verification should therefore not pollute future demo ranking data.
