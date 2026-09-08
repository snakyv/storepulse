# Requirements traceability

Status vocabulary: `PASS`, `PARTIAL`, `NOT IMPLEMENTED`, `NOT TESTED`.

A `PASS` is used only when the employer behavior itself is implemented and verified. Stage 05 now has a clean local end-to-end verification pass, including five-producer evidence, duplicate persistence proof, deterministic cleanup and backend state restoration. Stage 05 publication still remains pending until the amended commit receives a green GitHub Actions run. Statuses below remain `PARTIAL` where later analytics/load proof is required.

| Employer requirement | Current implementation | Verified proof | Status |
|---|---|---|---|
| Separate backend and frontend communicating over network | FastAPI + Vue over HTTP/WebSocket | verified foundation runtime | PASS |
| Python backend | Python 3.12 / FastAPI | quality gates and runtime | PASS |
| Vue or React frontend | Vue 3 + TypeScript | typecheck, Vitest, production build | PASS |
| Relational DB, preferably PostgreSQL | PostgreSQL 17 + SQLAlchemy/Alembic | readiness, migrations, seed, restart and clean bootstrap | PASS |
| Quick local deployment | Docker Compose + PowerShell scripts | clean-volume bootstrap | PASS |
| Two simultaneously open clients | WebSocket invalidation + REST refetch + fallback refresh | two-tab connectivity proof | PARTIAL; ranking realtime pending |
| Several POS simulators | Five Compose producers implement heartbeat + SALE/REFUND traffic | corrected local smoke observed durable traffic from exactly 5 stores | PASS |
| POS events contain product, quantity, amount and event time | SALE/REFUND contracts and producer payloads contain all fields | backend tests + five-producer local runtime PASS | PASS |
| Configurable sales event intensity | Per-store events-per-second environment controls | config unit tests + corrected five-producer smoke with overrides | PASS |
| Duplicate events do not create duplicate business events/metrics | Backend idempotency + simulator exact duplicate replay | producer replay observed and replayed event remained exactly 1 durable row; ranking metric effect pending | PARTIAL |
| Late events are assigned based on `occurred_at` | Producer backdates aware `occurred_at`; backend preserves it | 39 late rows persisted in the final isolated Stage 05 smoke; ranking assignment pending | PARTIAL |
| Refunds are generated and decrease metrics | Safe REFUND ingestion + bounded simulator refund generation | 19 durable REFUND rows observed in the final isolated Stage 05 smoke; analytics subtraction pending | PARTIAL |
| Live ranking | Not yet | — | NOT IMPLEMENTED |
| Last hour / today metrics | Not yet | — | NOT IMPLEMENTED |
| Revenue / sales / average check | Durable event rows exist; aggregation not yet implemented | ingestion proof only | NOT IMPLEMENTED |
| Leader / outsider / dynamics | Not yet | — | NOT IMPLEMENTED |
| Store detail / top products / plan progress | Seed has products/targets only | schema + seed | NOT IMPLEMENTED |
| Settings | Store fields exist; editing API/UI pending | store schema | PARTIAL |
| Offline store notification | heartbeat/status foundation only | connectivity proof | NOT IMPLEMENTED |
| Behind-plan notification | target/timezone fields prepared | store schema | NOT IMPLEMENTED |
| Local day closes at local midnight per store timezone | timezone field prepared | store schema | NOT IMPLEMENTED |
| Restart preserves today's ranking | PostgreSQL persistence foundation verified | seeded stores survived restart | PARTIAL; ranking itself not implemented |
| No lost events / no visible delay under five simulators | Retry-safe producer candidate + backend idempotency/refund locking | measured five-producer load proof pending | PARTIAL |
| Honest state description | Explicit current-state and limitation docs | this file + `PROJECT_STATE.md` | PASS |
| AI prompts / decision log | AI/development docs maintained | `docs/ai/` + `DEVELOPMENT_LOG.md` | PASS for current work |
| Git/time progression | Work isolated into verified feature commits | developer-confirmed green history through Stage 04 | PASS |
