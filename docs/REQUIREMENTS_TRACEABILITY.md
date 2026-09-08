# Requirements traceability

Status vocabulary: `PASS`, `PARTIAL`, `NOT IMPLEMENTED`, `NOT TESTED`.

A `PASS` is used only when the stated employer behavior itself is implemented and verified. A narrower foundation or ingestion proof is recorded explicitly without upgrading a broader unfinished requirement to `PASS`.

| Employer requirement | Current implementation | Verified proof | Status |
|---|---|---|---|
| Separate backend and frontend communicating over network | FastAPI + Vue over HTTP/WebSocket | Docker Compose runtime and API/browser use | PASS |
| Python backend | Python 3.12 / FastAPI | backend quality gates and runtime | PASS |
| Vue or React frontend | Vue 3 + TypeScript | typecheck, Vitest, production build | PASS |
| Relational DB, preferably PostgreSQL | PostgreSQL 17 + SQLAlchemy/Alembic | readiness, migration, seed, restart and clean bootstrap | PASS |
| Quick local deployment | Docker Compose + PowerShell scripts | clean-volume `dev.ps1` bootstrap reached healthy backend/frontend/PostgreSQL | PASS |
| Two simultaneously open clients | WebSocket invalidation + REST refetch + fallback refresh | developer manually verified two tabs update automatically on connectivity change | PARTIAL; realtime client foundation PASS, live ranking behavior pending |
| Several POS simulators | Five independent Compose simulator services | five containers ran concurrently and all heartbeats returned `200 OK` | PARTIAL; multi-instance runtime PASS, POS sales generation pending |
| POS events contain product, quantity, amount and event time | SALE request contract contains product SKU, quantity, integer `amount_cents` and timezone-aware `occurred_at` | Stage 03 schema/integration tests (`25 passed` total backend suite) | PARTIAL; backend ingestion PASS, simulator generation pending |
| Configurable sales event intensity | Not yet | — | NOT IMPLEMENTED |
| Duplicate events do not create duplicate business events/metrics | PostgreSQL-authoritative SALE idempotency; exact duplicate returns `200`, conflict returns `409` | sequential + 8-way concurrent identical + concurrent conflicting PostgreSQL tests | PARTIAL; duplicate row prevention PASS, ranking metric effect proof awaits analytics |
| Late events are assigned based on `occurred_at` | timezone-aware `occurred_at` is accepted and preserved independently from `received_at` | late SALE integration test | PARTIAL; ingestion timestamp semantics PASS, ranking-window assignment pending |
| Live ranking | Not yet | — | NOT IMPLEMENTED |
| Last hour / today metrics | Not yet | — | NOT IMPLEMENTED |
| Revenue / sales / average check | SALE rows are now persisted; aggregation not yet implemented | Stage 03 event ingestion proof | NOT IMPLEMENTED |
| Leader / outsider / dynamics | Not yet | — | NOT IMPLEMENTED |
| Store detail / top products / plan progress | Seed has products/targets only | schema + seed | NOT IMPLEMENTED |
| Settings | Store fields exist; editing API/UI pending | `stores` schema | PARTIAL |
| Refunds decrease metrics | `REFUND` remains rejected by the Stage 03 request schema until safe validation exists | explicit Stage 03 rejection test | NOT IMPLEMENTED |
| Offline store notification | heartbeat/status foundation only | five heartbeat simulators + connectivity UI | NOT IMPLEMENTED |
| Behind-plan notification | target/timezone fields prepared | store schema | NOT IMPLEMENTED |
| Local day closes at local midnight per store timezone | timezone field prepared | store schema | NOT IMPLEMENTED |
| Restart preserves today's ranking | PostgreSQL persistence foundation verified | five stores survived backend restart; clean DB bootstrap verified | PARTIAL; ranking itself is not implemented |
| No lost events / no visible delay under five simulators | ingestion concurrency safety exists, but five simulators are heartbeat-only | Stage 03 concurrency tests plus baseline five-container proof | PARTIAL; final five-producer sales/load proof pending |
| Honest state description | Explicit current-state and limitation docs | this file + `PROJECT_STATE.md` | PASS |
| AI prompts / decision log | AI/development docs maintained | `docs/ai/` + `DEVELOPMENT_LOG.md` | PASS for current work |
| Git/time progression | Real repository history starts from verified baseline and stages are isolated | foundation commit `a2bf2b7`; Stage 03 prepared as a separate feature commit | PASS for history discipline |
