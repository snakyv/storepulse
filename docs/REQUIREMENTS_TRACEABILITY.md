# Requirements traceability

Status vocabulary: `PASS`, `PARTIAL`, `NOT IMPLEMENTED`, `NOT TESTED`.

A `PASS` is used only when the stated employer behavior itself is implemented and verified. A narrower foundation or candidate implementation is recorded explicitly without upgrading broader unfinished behavior.

| Employer requirement | Current implementation | Verified proof | Status |
|---|---|---|---|
| Separate backend and frontend communicating over network | FastAPI + Vue over HTTP/WebSocket | verified foundation runtime | PASS |
| Python backend | Python 3.12 / FastAPI | quality gates and runtime | PASS |
| Vue or React frontend | Vue 3 + TypeScript | typecheck, Vitest, production build | PASS |
| Relational DB, preferably PostgreSQL | PostgreSQL 17 + SQLAlchemy/Alembic | readiness, migration, seed, restart and clean bootstrap | PASS |
| Quick local deployment | Docker Compose + PowerShell scripts | clean-volume bootstrap | PASS |
| Two simultaneously open clients | WebSocket invalidation + REST refetch + fallback refresh | developer manually verified two tabs on connectivity changes | PARTIAL; ranking realtime pending |
| Several POS simulators | Five independent Compose services | five heartbeat containers verified concurrently | PARTIAL; business event generation pending |
| POS events contain product, quantity, amount and event time | SALE/REFUND contracts contain SKU, strict quantity, integer amount and aware `occurred_at` | full Stage 04 Docker/PostgreSQL suite PASS (`47 passed`) | PASS |
| Configurable sales event intensity | Not yet | — | NOT IMPLEMENTED |
| Duplicate events do not create duplicate business events/metrics | PostgreSQL-authoritative idempotency for SALE and REFUND paths | SALE and REFUND duplicate/concurrency paths verified locally; ranking metric effect still pending | PARTIAL; metric proof pending |
| Late events are assigned based on `occurred_at` | SALE and REFUND preserve aware `occurred_at` independently from `received_at` | SALE + REFUND ingestion tests PASS locally | PARTIAL; ranking-window assignment pending |
| Live ranking | Not yet | — | NOT IMPLEMENTED |
| Last hour / today metrics | Not yet | — | NOT IMPLEMENTED |
| Revenue / sales / average check | Event rows are durable; aggregation not yet implemented | ingestion proof only | NOT IMPLEMENTED |
| Leader / outsider / dynamics | Not yet | — | NOT IMPLEMENTED |
| Store detail / top products / plan progress | Seed has products/targets only | schema + seed | NOT IMPLEMENTED |
| Settings | Store fields exist; editing API/UI pending | store schema | PARTIAL |
| Refunds decrease metrics | Stage 04 safely persists bounded, concurrency-safe REFUND events referencing original SALE | full local refund integration/concurrency suite PASS; analytics subtraction not yet implemented | PARTIAL |
| Offline store notification | heartbeat/status foundation only | connectivity proof | NOT IMPLEMENTED |
| Behind-plan notification | target/timezone fields prepared | store schema | NOT IMPLEMENTED |
| Local day closes at local midnight per store timezone | timezone field prepared | store schema | NOT IMPLEMENTED |
| Restart preserves today's ranking | PostgreSQL persistence foundation verified | seeded stores survived restart | PARTIAL; ranking itself not implemented |
| No lost events / no visible delay under five simulators | SALE idempotency and REFUND serialization are locally verified under concurrency | five-producer business-traffic/load proof pending | PARTIAL |
| Honest state description | Explicit current-state and limitation docs | this file + `PROJECT_STATE.md` | PASS |
| AI prompts / decision log | AI/development docs maintained | `docs/ai/` + `DEVELOPMENT_LOG.md` | PASS for current work |
| Git/time progression | Work is isolated into verified feature commits | foundation + documented staged roadmap | PASS for history discipline |
