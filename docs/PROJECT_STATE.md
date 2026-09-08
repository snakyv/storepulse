# Project state — Stage 03 idempotent SALE ingestion

**Verified foundation:** checkpoint 00e
**Foundation commit:** `a2bf2b7 chore: establish verified StorePulse foundation`
**Current feature candidate:** `feat(events): add idempotent POS sale ingestion`
**Date:** 2026-09-08

## Current status

The infrastructure/connectivity foundation is verified locally and in GitHub Actions. Stage 03 adds the first business write path: idempotent `SALE` ingestion through `POST /api/v1/events`. The complete Stage 03 developer-machine verification gate passed before commit. GitHub Actions for the Stage 03 commit is intentionally treated as a separate publication proof after push.

StorePulse remains intentionally incomplete as the full Case 5 solution: refund safety, POS sale generation, rankings, store analytics/settings and alerting are subsequent feature stages.

## Implemented through Stage 03

- Docker Compose topology for PostgreSQL, migration, seed, backend, frontend and five optional heartbeat simulators.
- FastAPI liveness/readiness endpoints.
- PostgreSQL-backed store list and heartbeat persistence.
- WebSocket invalidation with REST refetch on the Vue client.
- Initial relational schema for stores, products and POS events.
- Deterministic seed: five stores and ten products.
- `POST /api/v1/events` for `SALE` events.
- PostgreSQL-authoritative idempotency using the `pos_events.event_id` primary key plus `INSERT ... ON CONFLICT DO NOTHING`.
- First valid use of an `event_id`: `201 accepted`.
- Exact replay of the same logical SALE payload: `200 duplicate` with no second row.
- Reuse of an existing `event_id` with a different logical payload: `409 Conflict`.
- Timezone-aware `occurred_at` validation and independent PostgreSQL `received_at`.
- Late SALE ingestion preserves producer `occurred_at`; analytics assignment is deliberately deferred to the ranking stage.
- Accepted SALE updates store `last_seen_at` and emits an `events.changed` invalidation after commit.
- Unknown store/product validation and explicit rejection of premature `REFUND` payloads in the SALE-only stage.
- PostgreSQL integration tests for sequential duplicates/conflicts and concurrent identical/conflicting requests.
- Test cleanup for Stage 03 events so verification does not leave sale rows behind.
- GitHub Actions Docker smoke coverage for actual HTTP accepted/duplicate/conflict semantics.
- Committed frontend lockfile, `npm ci`, async SQLAlchemy lifecycle handling and cross-platform line-ending policy.

## Verified developer-machine evidence — Stage 03

The supplied Windows + Docker Desktop log proves the following on the exact Stage 03 candidate:

- Stage 03 synchronization into the working repository: **PASS**.
- `git diff --check`: **PASS**.
- Docker verification image build: **PASS**.
- PostgreSQL readiness: **PASS**.
- Alembic migration: **PASS**.
- Deterministic seed: **PASS**.
- Ruff: **PASS**.
- mypy: **PASS** (`10 source files`).
- Backend pytest: **PASS** (`25 passed`).
- The Stage 03 suite includes real PostgreSQL idempotency, late-timestamp and concurrency cases.
- Simulator compilation: **PASS**.
- Frontend dependency/version checks: **PASS**.
- Frontend typecheck: **PASS**.
- Frontend Vitest: **PASS** (`2 passed`).
- Frontend production build: **PASS**.
- Backend readiness smoke test: **PASS**.
- Seeded store API smoke test: **PASS** (exactly five stores).
- Full `scripts/verify.ps1` completion: **PASS**.

The Stage 03 GitHub Actions run is not claimed in this document before the feature commit is pushed. Repository workflow history is the authoritative publication evidence after push.

## Stage 03 semantics proven by tests

The current test suite proves the ingestion contract rather than merely checking route existence:

- a new SALE is persisted once;
- an exact retry returns duplicate and preserves the original `received_at`;
- a conflicting payload for the same `event_id` returns `409`;
- an existing-ID conflict takes precedence over validating new unknown references;
- unknown new store/product references return `404`;
- naive timestamps and `REFUND` payloads are rejected in this stage;
- a late SALE keeps its original `occurred_at`;
- eight concurrent identical requests resolve to one accepted row plus duplicate responses;
- two concurrent conflicting payloads resolve to one winner and one `409`.

## Requirements still not proven

Stage 03 does not claim completion of functionality that depends on later stages:

- refund validation, partial/full refund semantics and over-refund protection;
- configurable POS sale/refund generation from the five simulator instances;
- ranking by revenue, sales count and average check;
- rolling last-hour and per-store local-day windows;
- assigning late events into ranking windows using `occurred_at`;
- leader/outsider/dynamics;
- store detail analytics and persisted settings;
- offline incident lifecycle and notification outbox;
- local-noon behind-plan alerts;
- ranking persistence across restart;
- final five-producer load proof;
- automated Playwright two-client ranking proof.

## Next delivery block

After the Stage 03 commit is pushed and its GitHub Actions workflow is green, the next feature commit is:

```text
feat(refunds): enforce safe refund processing
```

See `docs/NEXT_STEPS.md` for the complete staged roadmap.
