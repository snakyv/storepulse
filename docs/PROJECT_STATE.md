# Project state — scaffold checkpoint 00e

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
- Committed frontend `package-lock.json`; Docker and CI now require `npm ci`.

## Real developer-machine verification — checkpoint 00d, 2026-09-08

The supplied Windows + Docker Desktop logs prove:

- Exact checkpoint 00d synchronization into the local repository: **PASS**.
- Git remote corrected to `https://github.com/snakyv/storepulse.git`: **PASS**.
- `frontend/package-lock.json` generated in Node `22.23.2-alpine`: **PASS**.
- npm resolution audit at lock generation: **PASS** (`0 vulnerabilities` reported by npm at that time).
- Docker verification images (backend/migrate/seed/frontend/simulator): **PASS**.
- PostgreSQL `17.11-alpine` startup: **PASS**.
- Alembic migration: **PASS**.
- Deterministic seed: **PASS**.
- Ruff: **PASS**.
- mypy: **PASS** (`9 source files`).
- Backend pytest: **FAIL** with `1 failed, 9 passed`.

The failing test itself was not a bad `404` assertion. The traceback proves a pooled asyncpg connection created in one pytest asyncio loop was reused from another loop: `Future ... attached to a different loop`. The suite previously used pytest-asyncio's default function-scoped event loop while the application intentionally keeps one pooled `AsyncEngine` per process.

Because `verify.ps1` is fail-fast, frontend dependency/typecheck/unit/build gates were **not reached** during that run. The frontend image itself did build successfully using the new lockfile.

## Checkpoint 00e corrections awaiting developer re-run

- `pytest-asyncio` test and async-fixture loop scope set to `session`, matching the single-event-loop application process.
- Added explicit `dispose_engine()` that closes the async SQLAlchemy pool and resets lazy engine/session-factory globals.
- FastAPI lifespan now disposes the engine during graceful application shutdown.
- Added a session-scoped pytest teardown fixture so pooled asyncpg connections are disposed before pytest closes its session event loop.
- `verify.ps1` now waits explicitly for PostgreSQL readiness before running migration/seed commands with `--no-deps`.
- `verify.ps1` requires the committed frontend lockfile and adds an API smoke check after all code-quality gates.
- Frontend Docker installation now always uses `npm ci`; the fallback `npm install` path was removed.
- GitHub Actions frontend installation now always uses `npm ci` and caches from the committed lockfile.
- GitHub Actions Python runtime aligned to exact Python `3.12.14`.
- TypeScript compiler settings now also reject unused locals, unused parameters and switch fallthrough.
- Documentation updated to stop claiming the lockfile is absent and to record the actual 00d failure.

These 00e changes are **NOT YET CLAIMED PASS** until `scripts/verify.ps1` is rerun on the developer machine.

## Generation-environment checks for checkpoint 00e

- Python syntax/bytecode compilation over backend, tests and simulator: **PASS**.
- Database-independent Python tests: **PASS** (`7 passed`).
- `frontend/package.json`, `package-lock.json` and `tsconfig.json` JSON parse: **PASS**.
- `docker-compose.yml` and GitHub Actions YAML parse: **PASS**.
- Frontend lockfile root metadata matches `package.json`: **PASS**.
- `.env`, `.git`, `.idea`, caches, `node_modules` and build outputs excluded from the generated checkpoint: **PASS**.
- Full Docker/PostgreSQL/npm runtime verification: **NOT AVAILABLE** in the generation environment, therefore not claimed.

## Not implemented

- Sale/refund ingestion API and business validation.
- Idempotency/conflicting duplicate behavior at API level.
- Analytics and ranking queries.
- Late-event corrections.
- Offline incidents and notification outbox.
- Midday target alerts.
- Settings editing and store detail pages.
- Email emulator.
- Playwright two-tab test.
- Load/concurrency/restart proof.

## Known scaffold limitations

- Five simulator services send heartbeats only; they intentionally do not fake completed POS behavior.
- Current frontend is a foundation dashboard, not the final product UI.
- Frontend has typecheck, Vitest and build gates; a dedicated ESLint gate can be added before final submission if it remains useful after the UI grows.
