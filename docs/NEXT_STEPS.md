# Delivery roadmap

Completed/published foundation work and verified Stage 03 SALE ingestion remain the base. Stage 04 safe refund processing has passed the full developer-machine verification gate and is ready for commit/push; its GitHub Actions run is still pending publication.

## Stage 04 — local gate PASS, publication pending

Planned commit:

```text
feat(refunds): enforce safe refund processing
```

Scope:

- discriminated SALE/REFUND request contract on `POST /api/v1/events`;
- required `original_event_id` for refunds;
- original event must be a SALE;
- refund store/product must match the original sale;
- cumulative quantity and amount must each stay within original sale limits;
- per-original `SELECT ... FOR UPDATE` serialization;
- post-lock idempotency re-check for concurrent exact retries;
- database-level SALE/REFUND original-reference invariants;
- sequential and concurrent over-refund tests;
- Docker CI smoke for accepted/duplicate/over-refund behavior.

`scripts/verify.ps1` has passed on the developer machine (`47 passed` backend tests plus all frontend/build/API-smoke gates). The remaining Stage 04 publication steps are diff/staging review, the isolated feature commit, push, and a green GitHub Actions run.

## Remaining isolated commits

```text
feat(simulator): generate resilient configurable POS traffic
feat(analytics): add timezone-aware store rankings
feat(stores): add store insights and persisted settings
feat(ui): build realtime ranking and store management dashboard
feat(alerts): add durable offline incident notifications
feat(alerts): add local-noon plan monitoring
test: prove concurrency realtime timezone and restart behavior
docs: finalize submission evidence and demo guide
```

## Delivery discipline

Every stage follows the same gate:

```text
implement
→ static audit
→ Ruff/mypy/typecheck
→ unit + integration tests
→ Docker verification
→ manual scenario when required
→ git diff review
→ commit
→ push
→ GitHub Actions green
→ next stage
```

Do not add Kafka, Redis, authentication or cloud infrastructure before mandatory Case 5 behavior is implemented and proven.
