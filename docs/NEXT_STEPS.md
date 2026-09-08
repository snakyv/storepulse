# Delivery roadmap

StorePulse will be developed as a sequence of isolated, reviewable commits. Every feature commit must pass the local verification gate, relevant manual/runtime scenarios and GitHub Actions before the next stage begins.

## Commit roadmap

### 02 — verified baseline documentation

```text
docs: record verified baseline and delivery roadmap
```

Scope:

- reconcile README/project-state/traceability with the completed checkpoint 00e proof;
- add `.gitattributes` so Windows development and Linux Docker/CI use deterministic line endings;
- publish the staged delivery roadmap below.

### 03 — idempotent SALE ingestion

```text
feat(events): add idempotent POS sale ingestion
```

Implement database-enforced event insertion, exact-duplicate acceptance, conflicting same-`event_id` `409`, validation and concurrency tests.

### 04 — refund safety

```text
feat(refunds): enforce safe refund processing
```

Implement original-sale validation, partial/full refunds, cumulative over-refund protection and concurrent-refund tests.

### 05 — POS traffic simulator

```text
feat(simulator): generate resilient configurable POS traffic
```

Generate configurable sales, retries with stable event IDs, duplicates, late events and refunds from five independent simulator instances.

### 06 — ranking analytics

```text
feat(analytics): add timezone-aware store rankings
```

Implement rolling last-hour and per-store local-day windows, net revenue, effective sales count, average check, leader/outsider and dynamics using `occurred_at`.

### 07 — store analytics and settings

```text
feat(stores): add store insights and persisted settings
```

Add time-series/top-products/plan-progress APIs plus persisted daily target, responsible person and ranking-window settings.

### 08 — product dashboard UI

```text
feat(ui): build realtime ranking and store management dashboard
```

Build ranking, store-detail and settings views while preserving REST-as-authority + WebSocket-invalidation realtime behavior.

### 09 — offline incidents and notification outbox

```text
feat(alerts): add durable offline incident notifications
```

Persist outage incidents and a transactional outbox so each outage produces at most one mock email while remaining restart-safe.

### 10 — local-noon plan monitoring

```text
feat(alerts): add local-noon plan monitoring
```

Evaluate each store after local noon and deduplicate behind-plan notifications per store/local date.

### 11 — final engineering proof

```text
test: prove concurrency realtime timezone and restart behavior
```

Add five-producer load/concurrency checks, duplicate race proof, refund race proof, timezone-boundary/late-event tests, ranking restart proof and automated two-browser-client E2E coverage.

### 12 — submission evidence

```text
docs: finalize submission evidence and demo guide
```

Finalize README/demo instructions, evidence matrix, exact test counts/results, known trade-offs and clean-room submission audit.

## Development rule

For every stage:

```text
implement
→ static review
→ Ruff/mypy/typecheck
→ unit/integration tests
→ Docker verification
→ relevant manual/E2E scenario
→ git diff review
→ commit
→ push
→ GitHub Actions green
→ next stage
```

Do not add Kafka, Redis, authentication or deployment infrastructure before the mandatory Case 5 behavior above is correct and proven.
