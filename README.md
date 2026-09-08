# StorePulse

StorePulse is the incremental engineering implementation for the Mad Devs Junior Agentic Developer take-home, Case 5: **Store Ranking**.

The repository contains a verified infrastructure baseline, verified Stage 03 idempotent SALE ingestion, and a locally verified Stage 04 safe-refund implementation. It is intentionally not presented as the finished assignment. Stage 04 has passed the complete developer-machine verification gate and is ready for its isolated feature commit; GitHub Actions for that commit are not claimed until the commit is pushed and the workflow completes.

**Verified baseline (2026-09-08, checkpoint 00e):** the local Windows + Docker Desktop verification pipeline passed, including Docker builds, PostgreSQL readiness, Alembic migrations, deterministic seed, Ruff, mypy, backend tests, simulator compilation, pinned frontend dependency checks, Vue typecheck, Vitest, production build and API smoke. Five simultaneous heartbeat simulator containers, two-tab automatic connectivity refresh, backend-restart persistence and clean-volume bootstrap were also verified. The foundation commit was published as `a2bf2b7 chore: establish verified StorePulse foundation`, and its GitHub Actions run was confirmed green by the developer.

## Implemented through locally verified Stage 04

- FastAPI backend with liveness/readiness endpoints.
- PostgreSQL persistence and Alembic migrations.
- Relational schema for stores, products and POS events.
- Deterministic seed with five stores and ten products.
- `POST /api/v1/events` with discriminated SALE/REFUND request bodies.
- PostgreSQL-authoritative `event_id` idempotency.
- Exact duplicate retries return `200 duplicate`; conflicting `event_id` reuse returns `409`.
- Timezone-aware producer `occurred_at` is preserved independently from database `received_at`.
- Safe REFUND candidate with required `original_event_id`.
- Original refund target must exist and be a SALE from the same store/product.
- Cumulative refund quantity and amount are bounded by the original sale.
- `SELECT ... FOR UPDATE` serializes refund-limit decisions per original sale.
- Post-lock event-ID recheck preserves exact-duplicate semantics under concurrent refund retries.
- Database check constraints enforce SALE/REFUND original-reference shape and prevent self-reference.
- WebSocket invalidation channel with REST refetch on the Vue client.
- Five Docker Compose simulator services that currently send heartbeats only.
- Local PowerShell workflow and GitHub Actions quality checks.
- Pinned frontend dependency graph through `package-lock.json` and `npm ci`.
- AI-usage, development, architecture and requirements-traceability documentation.
- Cross-platform line-ending policy through `.gitattributes`.

## Explicitly not implemented yet

Configurable POS sale/refund generation, ranking analytics, refund subtraction from ranking metrics, late-event ranking correction, offline incidents, notification outbox, midday plan alerts, store detail analytics, persisted settings UI and the final concurrency/E2E/restart proof for ranking behavior.

See `docs/PROJECT_STATE.md`, `docs/REQUIREMENTS_TRACEABILITY.md` and `docs/NEXT_STEPS.md`.

## Prerequisites

Verified target environment:

- Windows 11
- Python 3.12 for optional host development
- Node.js 22 / npm 10 for optional host frontend work
- Docker Desktop with Docker Compose

Pinned container/CI runtimes:

- Python `3.12.14`
- Node `22.23.2`
- PostgreSQL `17.11-alpine`

Ports:

- Frontend: `5173`
- Backend: `8000`
- PostgreSQL host mapping: `55432` (container `5432`)

The existing host port `5432` is deliberately not used.

## Quick start (PowerShell)

From the repository root:

```powershell
Copy-Item .env.example .env
.\scripts\dev.ps1
```

Open:

- Frontend: http://localhost:5173
- Backend Swagger: http://localhost:8000/docs
- Backend readiness: http://localhost:8000/api/v1/health/ready

Start the five heartbeat simulators:

```powershell
.\scripts\demo.ps1
```

## Local verification

```powershell
.\scripts\verify.ps1
```

The verification script rebuilds the exact source images, waits for PostgreSQL, applies all migrations, seeds deterministic data, runs Ruff/mypy/pytest, checks the simulator, validates pinned frontend dependencies, runs Vue typecheck/Vitest/build, then starts the backend and smoke-tests readiness plus the seeded store API.

The script uses Docker, so local PostgreSQL, `psql`, Poetry, pnpm, Redis, Kafka and Make are not required.

## Event API

SALE example:

```json
{
  "event_id": "2bc00f92-ec88-4c3c-9302-7d8754540706",
  "store_code": "MAD-MADRID",
  "product_sku": "COFFEE-001",
  "event_type": "SALE",
  "quantity": 2,
  "amount_cents": 1598,
  "occurred_at": "2026-09-08T18:20:00Z",
  "source_instance": "simulator-madrid-1"
}
```

REFUND example:

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
  "source_instance": "simulator-madrid-1"
}
```

See `docs/EVENT_INGESTION.md` and `docs/REFUNDS.md` for exact semantics.

## Architecture

```text
heartbeat simulators --HTTP--> FastAPI <--SALE/REFUND events-- POS clients/tests
                                 |
                                 +--transactions/row locks--> PostgreSQL
                                 |
                                 +--WebSocket invalidation--> Vue clients
```

PostgreSQL is authoritative; WebSocket messages only tell clients to refetch current state. Refund-limit concurrency is serialized by locking the original SALE row, not by process-local locks.

More detail: `docs/ARCHITECTURE.md`.

## Git history discipline

The real public history starts from verified work rather than fabricated chronology.

```text
a2bf2b7 chore: establish verified StorePulse foundation
docs: record verified baseline and delivery roadmap
feat(events): add idempotent POS sale ingestion
feat(refunds): enforce safe refund processing     # locally verified; pending publication
```

Exact SHAs for later commits are not invented before Git creates them. Each feature is committed only after the local verification gate passes, then independently validated in GitHub Actions.

## Dependency reproducibility

Python direct dependencies are pinned. The frontend dependency graph is committed in `frontend/package-lock.json`, Docker and CI use `npm ci`, TypeScript is pinned to `6.0.2`, and the frontend runtime is pinned to Node `22.23.2`.

## Stop

```powershell
.\scripts\stop.ps1
```

Database data is preserved. Use `docker compose down -v` only when intentionally deleting the StorePulse PostgreSQL volume.
