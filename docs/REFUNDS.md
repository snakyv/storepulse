# Refund processing contract — Stage 04

Stage 04 extends `POST /api/v1/events` with idempotent, concurrency-safe `REFUND` events. A refund is not a negative sale: it is its own immutable event that references the original `SALE` through `original_event_id`.

## Request contract

```json
{
  "event_id": "72e1828d-804f-4edf-8c2a-d52268514e9d",
  "store_code": "MAD-MADRID",
  "product_sku": "COFFEE-001",
  "event_type": "REFUND",
  "quantity": 1,
  "amount_cents": 799,
  "occurred_at": "2026-09-08T19:20:00Z",
  "original_event_id": "2bc00f92-ec88-4c3c-9302-7d8754540706",
  "source_instance": "simulator-madrid-1",
  "metadata": {
    "reason": "customer-return"
  },
  "note": null
}
```

`event_id` identifies the refund itself. `original_event_id` identifies the SALE being refunded. Both are UUIDs.

## Validation rules

A new refund is accepted only when all of the following are true:

- the referenced original event exists;
- the original event is a top-level `SALE`, not another refund;
- refund store equals the original sale store;
- refund product equals the original sale product;
- quantity and amount are strict positive integers;
- cumulative refunded quantity does not exceed original sale quantity;
- cumulative refunded amount does not exceed original sale amount;
- `occurred_at` is timezone-aware.

The service intentionally treats quantity and monetary limits independently. A request is rejected if either remaining quantity or remaining amount would be exceeded.

## Response semantics

```text
new valid refund                  -> 201 accepted
exact retry                       -> 200 duplicate
same event_id, different payload  -> 409 Conflict
missing original sale             -> 404
original_event_id points to refund-> 422
store/product mismatch            -> 422
cumulative quantity exceeded      -> 409
cumulative amount exceeded        -> 409
```

Exact duplicate equivalence includes `original_event_id` in addition to the common event fields. A duplicate never consumes the remaining refundable quantity/amount twice.

## Concurrency safety

The critical invariant is enforced per original sale, not with an in-memory lock.

```text
request A                     request B
    |                             |
    +-- SELECT original FOR UPDATE|
    |                             +-- waits on same SALE row
    +-- sum committed refunds     |
    +-- validate remaining        |
    +-- insert REFUND             |
    +-- COMMIT                    |
                                  +-- acquires SALE row lock
                                  +-- re-check event_id
                                  +-- sum now-committed refunds
                                  +-- validate remaining
                                  +-- accept or 409
```

The row lock serializes refund-limit decisions for one original sale while still allowing refunds for unrelated sales to proceed independently.

There is a deliberate idempotency re-check after acquiring the original-sale lock. Without it, an identical concurrent retry that waited behind the first request could count the already-committed refund and then incorrectly reject itself as an over-refund instead of returning `200 duplicate`.

The refund insert still uses the `event_id` primary key plus PostgreSQL `ON CONFLICT DO NOTHING`, so event identity remains database-authoritative even for requests racing across different originals.

## Database invariants

Migration `20260908_0002_refund_invariants.py` adds two database-level checks:

- `SALE` rows must have `original_event_id IS NULL`, while `REFUND` rows must have an original reference;
- an event cannot reference itself as its original event.

Cross-row rules such as “original must be SALE”, same store/product, and cumulative limits cannot be expressed as simple row CHECK constraints. They are enforced transactionally by the ingestion service while locking the referenced sale.

## Event time and later analytics

A refund preserves its producer-supplied timezone-aware `occurred_at` independently from database `received_at`, including late refunds. The future analytics stage will subtract refunds according to `occurred_at`, not reception time.

Stage 04 does **not** yet claim ranking effects. It makes refund events safe and durable so the analytics stage can consume them correctly.

## Verification status

The Stage 04 developer-machine gate passed in the pinned Docker/PostgreSQL environment on 2026-09-09:

- Alembic upgrade to `20260908_0002`: PASS;
- Ruff: PASS;
- mypy: PASS (`10 source files`);
- full backend pytest suite: PASS (`47 passed`);
- frontend typecheck/Vitest/production build regression gates: PASS;
- backend readiness and seeded-store API smoke: PASS;
- complete `scripts/verify.ps1`: PASS.

This proves the refund ingestion and concurrency safeguards in the local target environment. It does not yet prove refund subtraction from rankings, because ranking analytics are deliberately deferred to a later feature stage. GitHub Actions for the Stage 04 commit are not claimed until publication.
