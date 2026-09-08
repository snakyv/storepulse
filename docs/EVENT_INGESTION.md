# POS event ingestion contract — Stage 03

Stage 03 introduces the first business write path: idempotent `SALE` ingestion through `POST /api/v1/events`.

Refund processing is intentionally deferred to the next feature stage. A request with `event_type: "REFUND"` is rejected by the Stage 03 request schema rather than being silently stored without refund validation.

## Request contract

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

Validation rules in this stage:

- `event_id` is a UUID supplied by the producer and is the idempotency identity.
- `event_type` must be `SALE`.
- `quantity` and `amount_cents` are strict positive integers.
- `occurred_at` must include timezone information.
- `store_code`, `product_sku` and `source_instance` must be non-empty and fit persisted field limits.
- unknown stores/products return `404` for a new event ID.
- additional request fields are rejected instead of being ignored.

Money remains integer minor units; floating-point currency values are not accepted.

## Idempotency semantics

The PostgreSQL primary key on `pos_events.event_id` is authoritative. The ingestion path uses PostgreSQL `INSERT ... ON CONFLICT DO NOTHING`, not a check-then-insert race as its final authority.

For a previously unseen `event_id`:

```text
POST /api/v1/events
→ PostgreSQL INSERT ... ON CONFLICT DO NOTHING
→ one row committed
→ 201 accepted
```

For the same `event_id` with the same immutable logical payload:

```text
first request  → 201 accepted
retry          → 200 duplicate
row count      → still 1
received_at    → original value is returned
```

For the same `event_id` with any different logical payload field:

```text
→ 409 Conflict
→ original row remains unchanged
```

The duplicate comparison includes store, product, event type, quantity, amount, `occurred_at`, source instance, metadata and note. `received_at` is not part of the producer payload and therefore is not part of duplicate equivalence.

When two requests race for a new `event_id`, PostgreSQL decides which insert wins. A losing request re-reads the committed row and classifies itself as an exact duplicate or a conflicting reuse of the ID. Integration tests cover both concurrent-identical and concurrent-conflicting requests.

## Event time

`occurred_at` is stored exactly as the timezone-aware business event instant supplied by the producer. `received_at` is assigned by PostgreSQL when the event is inserted.

A late event is therefore represented as:

```text
occurred_at < received_at
```

Stage 03 proves that this timestamp is preserved. Ranking windows will deliberately use `occurred_at` in the analytics stage.

## Connectivity and realtime invalidation

A newly accepted sale also updates the store's `last_seen_at` to the event's database reception timestamp. After the database transaction commits, the API broadcasts an `events.changed` invalidation message.

WebSocket messages remain non-authoritative: clients refetch REST state after an invalidation. Exact duplicate retries and conflicting requests do not broadcast a business-state change because they do not create a new event row.

## Test isolation

Stage 03 integration tests exercise the real PostgreSQL ingestion path. Test events use a reserved `pytest:sale-ingestion:` source prefix and are removed by an async fixture. The fixture also restores each store's original `last_seen_at`, so a successful test run does not leave demo ranking/connectivity data behind.
