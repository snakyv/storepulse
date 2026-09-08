# StorePulse

StorePulse is the incremental engineering implementation for the Mad Devs Junior Agentic Developer take-home, Case 5: **Store Ranking**.

The repository currently contains a **verified foundation baseline** for the later POS-event, ranking, refund and alerting work. It is intentionally not presented as the finished assignment.

**Verified baseline (2026-09-08, checkpoint 00e):** the complete local verification pipeline passed on Windows + Docker Desktop, including Docker image builds, PostgreSQL readiness, Alembic migrations, deterministic seed, Ruff, mypy, `10/10` backend tests, simulator compilation, pinned frontend dependency checks, Vue typecheck, `2/2` Vitest tests, production build and a five-store API smoke test. The developer also verified five simultaneous heartbeat simulator containers, automatic updates in two browser tabs, backend-restart persistence, and a clean bootstrap after deleting the project PostgreSQL volume. The same baseline was committed as `a2bf2b7 chore: establish verified StorePulse foundation`, pushed to `origin/main`, and the corresponding GitHub Actions run was confirmed green by the developer.

## Implemented in the verified foundation

- FastAPI backend with liveness and PostgreSQL readiness endpoints.
- PostgreSQL persistence and Alembic initial migration.
- Initial relational schema for stores, products and POS events.
- Idempotent deterministic seed with five demo stores and ten products.
- Store list endpoint and heartbeat endpoint.
- WebSocket invalidation channel; heartbeat changes refresh multiple open clients without manual reload.
- Vue 3 + TypeScript dashboard shell showing store connectivity.
- Five Docker Compose simulator services that currently send heartbeats only.
- Local PowerShell workflow and GitHub Actions quality checks.
- Pinned frontend dependency graph through `package-lock.json` and `npm ci`.
- AI-usage, development, architecture and requirements-traceability documentation.
- Cross-platform line-ending policy through `.gitattributes`.

## Explicitly not implemented yet

Sales ingestion, duplicate/conflict handling, refunds, ranking analytics, late-event correction, offline incidents, notification outbox, midday plan alerts, store detail analytics, persisted settings UI and the final concurrency/E2E/restart proof for ranking behavior.

See `docs/PROJECT_STATE.md`, `docs/REQUIREMENTS_TRACEABILITY.md` and `docs/NEXT_STEPS.md`.

## Prerequisites

Verified target environment:

- Windows 11
- Python 3.12 for optional host development
- Node.js 22 / npm 10 for optional host frontend work
- Docker Desktop with Docker Compose

Pinned container/CI runtimes for this baseline:

- Python `3.12.14`
- Node `22.23.2`
- PostgreSQL `17.11-alpine`

Ports expected by the project:

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

Within roughly one heartbeat interval, the five store cards should show `ONLINE`. Open the dashboard in two tabs: heartbeat-triggered WebSocket invalidations and the fallback refresh keep both tabs synchronized.

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

## Verified runtime scenarios

The foundation baseline has also been exercised outside the automated quality gate:

- five heartbeat simulator containers running concurrently;
- all five simulators receiving `200 OK` from the heartbeat endpoint;
- two browser tabs updating automatically when store connectivity changes;
- five seeded stores still present after a backend restart;
- clean bootstrap after `docker compose --profile demo down -v`;
- complete `scripts/verify.ps1` pass again after the clean bootstrap.

These proofs cover the current connectivity/persistence foundation only. They do **not** claim that sales ranking, refund behavior or ranking restart persistence are complete before those features exist.

## Stop

```powershell
.\scripts\stop.ps1
```

Database data is preserved. To intentionally delete project data, use `docker compose down -v` only after understanding that it removes the StorePulse PostgreSQL volume.

## Architecture

```text
heartbeat simulators --HTTP--> FastAPI --transaction--> PostgreSQL
                                 |
                                 +--WebSocket invalidation--> Vue clients
```

PostgreSQL is authoritative; WebSocket messages only tell clients to refetch current state. The backend owns one lazily created async SQLAlchemy engine per process and disposes it on application shutdown.

More detail: `docs/ARCHITECTURE.md`.

## Git history

The real public history starts from the verified baseline rather than from generated fake chronology.

Current foundation commit:

```text
a2bf2b7 chore: establish verified StorePulse foundation
```

The next documentation-only commit records the completed verification evidence and delivery roadmap:

```text
docs: record verified baseline and delivery roadmap
```

Feature work will then proceed in isolated, tested commits; see `docs/NEXT_STEPS.md`.

## Dependency reproducibility

Python direct dependencies are pinned. The frontend dependency graph is committed in `frontend/package-lock.json`, Docker and CI use `npm ci`, TypeScript is pinned to `6.0.2`, and the frontend runtime is pinned to Node `22.23.2`.
