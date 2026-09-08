# Project state — verified foundation baseline

**Baseline:** checkpoint 00e
**Verified commit:** `a2bf2b7 chore: establish verified StorePulse foundation`
**Date:** 2026-09-08

## Current status

The infrastructure/connectivity foundation is verified locally and in GitHub Actions. StorePulse is still intentionally incomplete as a Case 5 solution: POS sales, refunds, rankings, store analytics and alerting are the next implementation stages.

## Implemented in source

- Docker Compose topology for PostgreSQL, migration, seed, backend, frontend and five optional heartbeat simulators.
- FastAPI liveness/readiness endpoints.
- PostgreSQL-backed store list.
- Store heartbeat persistence.
- WebSocket `stores.changed` invalidation after heartbeat commit.
- Vue dashboard shell that refetches store state on WebSocket invalidation and periodically refreshes time-derived connectivity state.
- Initial schema for stores, products and POS events.
- Deterministic idempotent seed: five stores, ten products.
- Python unit/integration tests, frontend unit tests, GitHub Actions workflow and PowerShell verification workflow.
- Committed frontend `package-lock.json`; Docker and CI require `npm ci`.
- Explicit async SQLAlchemy engine disposal and pytest session-loop lifecycle.
- Cross-platform line-ending policy in `.gitattributes`.

## Verified developer-machine evidence — checkpoint 00e

The supplied Windows + Docker Desktop logs prove the following for the current foundation:

- Checkpoint 00e synchronization into the local repository: **PASS**.
- Docker verification image build: **PASS**.
- PostgreSQL `17.11-alpine` readiness: **PASS**.
- Alembic migration: **PASS**.
- Deterministic seed: **PASS**.
- Ruff: **PASS**.
- mypy: **PASS** (`9 source files`).
- Backend pytest: **PASS** (`10 passed`).
- Simulator compilation: **PASS**.
- Frontend dependency tree/version checks: **PASS**.
- Frontend typecheck: **PASS**.
- Frontend Vitest: **PASS** (`2 passed`).
- Frontend production build: **PASS**.
- Backend readiness smoke test: **PASS**.
- Seeded stores API smoke test: **PASS** (exactly five stores).
- Five simulator containers running concurrently: **PASS**.
- Heartbeat delivery from all five simulators: **PASS** (`200 OK`).
- Two-browser-tab automatic connectivity refresh: **PASS** (developer manual verification).
- Backend restart persistence for seeded store state: **PASS** (`5` stores before and after restart).
- Clean bootstrap after deleting the StorePulse PostgreSQL volume: **PASS**.
- Full verification rerun after clean bootstrap: **PASS**.

The developer then committed the verified baseline as `a2bf2b7`, pushed it to `origin/main`, and confirmed the corresponding GitHub Actions workflow completed successfully.

## What the verified foundation does not prove yet

The current runtime proofs are deliberately scoped to the foundation. They do not yet prove employer requirements that depend on business functionality which has not been implemented:

- sales-event ingestion and API-level idempotency/conflicting duplicate semantics;
- refund validation and over-refund protection;
- ranking by revenue, sales count and average check;
- rolling last-hour and per-store local-day windows;
- late-event correction based on `occurred_at`;
- leader/outsider/dynamics;
- store detail analytics and persisted settings;
- offline incident lifecycle and notification outbox;
- local-noon behind-plan alerts;
- ranking persistence across restart;
- final five-producer concurrency/load proof;
- automated Playwright two-client ranking proof.

## Known foundation limitations

- The five simulator services send heartbeats only; they do not yet generate POS sales/refunds.
- The current frontend is a connectivity foundation, not the final ranking product UI.
- PostgreSQL is already the source of truth, but ranking persistence cannot be claimed until ranking exists.
- The two-tab manual proof validates the realtime transport/refetch foundation, not yet live sales ranking.

## Next delivery block

The next feature commit is intentionally focused on the core event contract:

```text
feat(events): add idempotent POS sale ingestion
```

See `docs/NEXT_STEPS.md` for the complete staged commit roadmap.
