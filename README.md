# StorePulse

StorePulse is the incremental engineering implementation for the Mad Devs Junior Agentic Developer take-home, Case 5: **Store Ranking**.

This checkpoint intentionally implements only the verified foundation required for later POS-event, ranking and alerting work. It is **not** the finished assignment.

**Revision note (2026-09-08, checkpoint 00e):** the developer-machine rerun of checkpoint 00d proved Docker image builds, PostgreSQL startup, migrations, deterministic seed, Ruff and mypy. Backend pytest reached `9 passed / 1 failed`; the remaining failure was caused by a pooled SQLAlchemy `AsyncEngine` being reused by pytest across different function-scoped asyncio event loops. Checkpoint 00e aligns the async test suite to one session-scoped event loop (matching the single-loop application model), adds explicit engine disposal, requires the committed npm lockfile, strengthens PostgreSQL readiness handling in local verification and keeps CI aligned with the same pinned runtimes. The complete Docker verification must be rerun before the first commit.

## Implemented in this scaffold

- FastAPI backend with liveness and PostgreSQL readiness endpoints.
- PostgreSQL persistence and Alembic initial migration.
- Initial relational schema for stores, products and POS events.
- Idempotent deterministic seed with five demo stores and ten products.
- Store list endpoint and heartbeat endpoint.
- WebSocket invalidation channel; heartbeat changes can refresh multiple open clients without manual reload.
- Vue 3 + TypeScript dashboard shell showing store connectivity.
- Five Docker Compose simulator services that currently send heartbeats only.
- Local PowerShell workflow and GitHub Actions quality checks.
- Pinned frontend dependency graph through `package-lock.json` and `npm ci`.
- Initial AI-usage, development, architecture and requirements-traceability documentation.

## Explicitly not implemented yet

Sales ingestion, duplicate/conflict handling, refunds, ranking analytics, late-event correction, offline incidents, notification outbox, midday plan alerts, store detail analytics, settings UI and final E2E/load/restart proofs.

See `docs/PROJECT_STATE.md` and `docs/NEXT_STEPS.md`.

## Prerequisites

Verified target environment:

- Windows 11
- Python 3.12 for optional host development
- Node.js 22 / npm 10 for optional host frontend work
- Docker Desktop with Docker Compose

Pinned container/CI runtimes for this checkpoint:

- Python `3.12.14`
- Node `22.23.2`
- PostgreSQL `17.11-alpine`

Ports expected by the scaffold:

- Frontend: `5173`
- Backend: `8000`
- PostgreSQL host mapping: `55432` (container port `5432`)

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

Within roughly one heartbeat interval, the five store cards should show `ONLINE`. Open the dashboard in two tabs: heartbeat-triggered WebSocket invalidations should refresh both tabs.

## Local verification

```powershell
.\scripts\verify.ps1
```

The verification script:

1. validates Docker Compose configuration;
2. rebuilds the exact current source images;
3. starts PostgreSQL and waits for `pg_isready`;
4. applies migrations and deterministic seed;
5. runs Ruff, mypy and pytest;
6. compiles the simulator;
7. verifies the pinned frontend dependency tree and tool versions;
8. runs Vue typecheck, Vitest and the production build;
9. starts the backend and smoke-tests readiness plus the five-store API result.

The script uses Docker, so local PostgreSQL, `psql`, Poetry, pnpm, Redis, Kafka and Make are not required.

## Stop

```powershell
.\scripts\stop.ps1
```

Database data is preserved. To intentionally delete project data later, use `docker compose down -v` only after understanding that it removes the StorePulse PostgreSQL volume.

## Architecture

```text
heartbeat simulators --HTTP--> FastAPI --transaction--> PostgreSQL
                                 |
                                 +--WebSocket invalidation--> Vue clients
```

PostgreSQL is authoritative; WebSocket messages only tell clients to refetch current state. The backend owns one lazily created async SQLAlchemy engine per process and disposes it on application shutdown.

More detail: `docs/ARCHITECTURE.md`.

## Git history

Generated checkpoints intentionally contain no fabricated `.git` history. The developer's real local repository is preserved when applying checkpoint updates. Make the first commit only after the complete local verification succeeds.

Suggested first commit after successful local verification:

```text
chore: bootstrap StorePulse foundation
```

## Dependency reproducibility

Python direct dependencies are pinned. The frontend dependency graph is committed in `frontend/package-lock.json`, Docker and CI use `npm ci`, TypeScript is pinned to `6.0.2`, and the frontend runtime is pinned to Node `22.23.2`.
