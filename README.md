# StorePulse

[![CI](https://github.com/snakyv/storepulse/actions/workflows/ci.yml/badge.svg)](https://github.com/snakyv/storepulse/actions/workflows/ci.yml)

StorePulse is the incremental engineering implementation for the Mad Devs Junior Agentic Developer take-home, Case 5: **Store Ranking**.

The repository is developed as a sequence of isolated, verified feature commits rather than as one opaque final dump. The verified public history currently includes the infrastructure baseline, idempotent SALE ingestion and concurrency-safe REFUND processing. Stage 05 now has a clean end-to-end local PASS for repository-wide quality gates, backend/simulator/frontend regression checks, five-producer traffic evidence, deterministic cleanup and backend state restoration. Stage 05 remains outside the verified public baseline only until the amended commit is pushed and the corresponding GitHub Actions run is green.

## Verified public baseline

The developer has confirmed green local verification and green GitHub Actions through:

```text
chore: establish verified StorePulse foundation
docs: record verified baseline and delivery roadmap
feat(events): add idempotent POS sale ingestion
feat(refunds): enforce safe refund processing
```

Exact commit SHAs are not invented in documentation when they were not supplied to the artifact-generation environment.

## Implemented before Stage 05

- FastAPI backend with liveness/readiness endpoints.
- PostgreSQL persistence and Alembic migrations.
- Relational schema for stores, products and immutable POS events.
- Deterministic seed with five stores and ten products.
- `POST /api/v1/events` with discriminated SALE/REFUND request bodies.
- PostgreSQL-authoritative `event_id` idempotency.
- Exact duplicate retries return `200 duplicate`; conflicting `event_id` reuse returns `409`.
- Timezone-aware producer `occurred_at` is preserved independently from database `received_at`.
- REFUND requires a valid original SALE from the same store and product.
- Cumulative refund quantity and amount are bounded by the original sale.
- `SELECT ... FOR UPDATE` serializes concurrent refund-limit decisions per original sale.
- Database checks enforce SALE/REFUND original-reference shape and prevent self-reference.
- WebSocket invalidation channel with REST refetch on the Vue client.
- Local PowerShell workflow and GitHub Actions quality gates.
- Pinned frontend dependency graph through `package-lock.json` and `npm ci`.
- Cross-platform line-ending policy through `.gitattributes`.

## Stage 05: real POS traffic — local end-to-end PASS, publication pending

The five Compose simulator services now generate business traffic instead of heartbeats only.

Each producer supports:

- independently configurable events-per-second intensity;
- valid SALE generation over the seeded product catalog;
- REFUND generation against sales already acknowledged by that simulator;
- exact duplicate replays;
- configurable late `occurred_at` generation;
- retry of transient network/server failures with the **same** event ID and payload;
- exponential backoff with jitter;
- bounded outbound queue and producer backpressure;
- independent heartbeat loop;
- deterministic per-store random seeds for reproducible smoke behavior;
- periodic runtime statistics.

The stage also adds simulator unit tests plus a five-container business-traffic smoke to both local verification and GitHub Actions.

The final local `scripts/verify.ps1` run completed successfully in the developer's pinned Windows/Docker/PostgreSQL environment on 2026-09-09. Repository-wide Ruff passed, mypy passed, all `47` backend tests passed, all `9` simulator unit tests passed, all `16` shared verification-helper regression tests passed, and frontend typecheck/Vitest/build passed. The isolated five-producer run `verify-dd56b81aafad` observed traffic from exactly five stores with `20` SALE rows, `19` REFUND rows and `39` late rows, observed an exact duplicate replay, and confirmed exactly `1` durable PostgreSQL row for the replayed `event_id`. The write barrier, verification-data cleanup, backend restart readiness, post-restart run isolation and store connectivity restore all reported PASS before the script ended with `Verification completed.`

Stage 05 is therefore **LOCAL END-TO-END PASS**. The first published candidate's GitHub Actions run exposed a repository-wide Ruff-scope mismatch; the subsequent hardening work centralized Ruff targets and simulator smoke behavior so local verification and CI now execute the same Python contracts. The only remaining Stage 05 publication gate is to amend the existing feature commit with this verified candidate, push it with `--force-with-lease`, and require the resulting GitHub Actions run to be green before Stage 05 is added to the verified public baseline.

See `docs/SIMULATOR.md` for exact producer semantics.

## Explicitly not implemented yet

Ranking analytics, refund subtraction from ranking metrics, last-hour/local-day windows, leader/outsider/dynamics, store detail analytics, persisted settings UI, offline incidents, notification outbox, local-noon plan alerts and final concurrency/E2E/restart ranking proof remain later stages.

See `docs/PROJECT_STATE.md`, `docs/REQUIREMENTS_TRACEABILITY.md` and `docs/NEXT_STEPS.md`.

## Prerequisites

Verified target environment:

- Windows 11
- Python 3.12+ on the host for verification helpers and optional development
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

Start the five POS producers:

```powershell
.\scripts\demo.ps1
```

Watch traffic:

```powershell
docker compose --profile demo logs -f `
    simulator-madrid `
    simulator-london `
    simulator-new-york `
    simulator-tokyo `
    simulator-warsaw
```

Tune traffic in `.env`, for example:

```text
SIMULATOR_MADRID_EVENTS_PER_SECOND=2.0
SIMULATOR_LONDON_EVENTS_PER_SECOND=0.5
SIMULATOR_REFUND_RATE=0.20
SIMULATOR_DUPLICATE_RATE=0.08
SIMULATOR_LATE_EVENT_RATE=0.10
```

## Local verification

```powershell
.\scripts\verify.ps1
```

The verification script rebuilds the exact source images, waits for PostgreSQL, applies migrations, seeds deterministic data, runs the shared repository-wide Ruff gate plus mypy/backend pytest, compiles and unit-tests the simulator, validates pinned frontend dependencies, runs Vue typecheck/Vitest/build, starts the backend and smoke-tests the seeded store API. `scripts/run_ruff.py` is the single source of truth for Ruff targets in both Windows/Docker verification and GitHub Actions; it uses the explicit backend Ruff configuration and `--no-cache`, so the local source tree can stay mounted read-only without cache-write failures.

Stage 05 simulator proof is centralized in `scripts/verify_simulator_smoke.py`, which is invoked by both local verification and GitHub Actions. It recreates all five POS simulators under deterministic elevated smoke settings, assigns each run a unique tag, polls durable PostgreSQL evidence for SALE, REFUND and late-event traffic, and proves an exact duplicate replay still has one durable row. Before cleanup it verifies producer termination, establishes a backend write barrier by stopping the backend, executes FK-safe REFUND-before-SALE cleanup inside an explicit PostgreSQL transaction, verifies zero verification rows remain, restores the pre-smoke `last_seen_at` and `updated_at` snapshot through typed PostgreSQL JSON records, restarts the backend, waits for readiness, and re-verifies both run isolation and restored store state. Docker/psql stdout and stderr are preserved for diagnostics rather than discarded.

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
  "source_instance": "simulator-madrid:example"
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
  "source_instance": "simulator-madrid:example"
}
```

See `docs/EVENT_INGESTION.md` and `docs/REFUNDS.md` for backend semantics.

## Architecture

```text
five POS simulators --HTTP SALE/REFUND--> FastAPI
       |                                   |
       +--heartbeat----------------------->|
                                           +--transactions/row locks--> PostgreSQL
                                           |
                                           +--WebSocket invalidation--> Vue clients
```

PostgreSQL is authoritative. WebSocket messages only tell clients to refetch current state. Producer retries reuse the same immutable event identity; backend idempotency is therefore the reliability boundary for ambiguous HTTP outcomes.

More detail: `docs/ARCHITECTURE.md` and `docs/SIMULATOR.md`.

## Development discipline

Each feature follows:

```text
implement
→ static audit
→ quality/unit/integration tests
→ Docker verification
→ manual proof when needed
→ git diff review
→ isolated commit
→ push
→ GitHub Actions green
→ next stage
```

No Redis, Kafka, authentication or cloud infrastructure is added before mandatory Case 5 behavior is implemented and proven.

## Stop

```powershell
.\scripts\stop.ps1
```

Database data is preserved. Use `docker compose down -v` only when intentionally deleting the StorePulse PostgreSQL volume.
