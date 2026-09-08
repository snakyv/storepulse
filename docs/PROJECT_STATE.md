# Project state — Stage 04 safe refund processing locally verified

**Verified foundation:** checkpoint 00e
**Foundation commit:** `a2bf2b7 chore: establish verified StorePulse foundation`
**Verified feature base:** Stage 03 idempotent SALE ingestion passed the full developer-machine gate before publication.
**Current feature:** `feat(refunds): enforce safe refund processing`
**Date:** 2026-09-09

## Current status

Stage 04 extends the verified SALE-ingestion base with idempotent REFUND events, original-sale validation, cumulative refund limits, PostgreSQL row locking and database-level reference invariants.

The complete developer-machine verification gate has now passed against the pinned Docker/PostgreSQL environment, including migration `20260908_0002`, Ruff, mypy, the full backend test suite, frontend regression gates and the backend API smoke. The Stage 04 feature is therefore locally accepted and ready for its isolated commit. GitHub Actions for that commit remain **NOT TESTED** until the commit is pushed and the workflow actually completes.

StorePulse remains incomplete as the full Case 5 solution: configurable POS traffic, rankings, store analytics/settings and alerting are later stages.

## Implemented through locally verified Stage 04

- Separate FastAPI/Vue services with PostgreSQL persistence and Docker Compose.
- Deterministic five-store / ten-product seed.
- WebSocket invalidation with REST refetch.
- Idempotent `SALE` ingestion with PostgreSQL `event_id` authority.
- Discriminated `SALE` / `REFUND` body on `POST /api/v1/events`.
- Refund requires `original_event_id`.
- Referenced original must exist and be a top-level SALE.
- Refund store and product must match the original sale.
- Cumulative refunded quantity cannot exceed sale quantity.
- Cumulative refunded amount cannot exceed sale amount.
- Refund decisions for the same original sale are serialized with `SELECT ... FOR UPDATE`.
- Event ID is re-checked after waiting for the original-sale lock so an identical concurrent retry returns duplicate instead of being double-counted against refund limits.
- Exact REFUND replay returns `200 duplicate`; conflicting reuse of its `event_id` returns `409`.
- Late REFUND preserves producer `occurred_at` independently from `received_at`.
- Migration `20260908_0002_refund_invariants.py` adds database checks for SALE/REFUND original-reference shape and self-reference prevention.
- New tests cover partial/full refunds, mismatched references, chained-refund rejection, sequential limit enforcement, exact duplicate behavior and concurrent over-refund races.
- GitHub Actions Docker smoke is extended to exercise real HTTP SALE + REFUND accepted/duplicate/over-limit behavior after publication.

## Stage 04 verification

Developer-machine verification on Windows + Docker Desktop:

- Docker image build: PASS.
- PostgreSQL readiness: PASS.
- Alembic upgrade `20260908_0001 -> 20260908_0002`: PASS.
- Deterministic seed: PASS.
- Ruff: PASS.
- mypy: PASS (`10 source files`).
- Backend pytest: PASS (`47 passed`).
- Simulator compile: PASS.
- Frontend dependency/version checks: PASS.
- Frontend typecheck: PASS.
- Frontend Vitest: PASS (`2 passed`).
- Frontend production build: PASS.
- Backend readiness: PASS.
- Seeded-store API smoke: PASS (exactly five stores).
- Complete `scripts/verify.ps1`: PASS.

Artifact-generation checks performed before the developer run also passed Python compile, database-independent pytest (`16 passed` with integration tests deselected), FastAPI OpenAPI generation and SALE/REFUND discriminator/response-contract inspection.

Publication status: local Stage 04 gate PASS; GitHub Actions remain NOT TESTED until the feature commit is pushed.

## Requirements still not complete after Stage 04

Safe refund ingestion is a prerequisite for later metrics, but Stage 04 does not yet implement:

- simulator-generated SALE/REFUND traffic and configurable intensity;
- ranking by revenue, sales count and average check;
- refund subtraction from ranking metrics;
- rolling last-hour and per-store local-day windows;
- leader/outsider/dynamics;
- store detail analytics and persisted settings;
- offline incident lifecycle and notification outbox;
- local-noon behind-plan alerts;
- final five-producer load proof;
- automated Playwright two-client ranking proof.

## Next delivery block

After committing/pushing this locally verified Stage 04 feature and confirming green GitHub Actions, the next isolated feature commit is:

```text
feat(simulator): generate resilient configurable POS traffic
```

See `docs/NEXT_STEPS.md` for the complete roadmap.
