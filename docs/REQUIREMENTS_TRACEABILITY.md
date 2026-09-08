# Requirements traceability

Status vocabulary: `PASS`, `PARTIAL`, `NOT IMPLEMENTED`, `NOT TESTED`.

A `PASS` is used only when the stated employer behavior itself is implemented and verified. Foundation proofs are recorded explicitly without upgrading a broader unfinished requirement to `PASS`.

| Employer requirement | Current implementation | Verified proof | Status |
|---|---|---|---|
| Separate backend and frontend communicating over network | FastAPI + Vue over HTTP/WebSocket | Docker Compose runtime and API/browser use | PASS |
| Python backend | Python 3.12 / FastAPI | backend quality gates and runtime | PASS |
| Vue or React frontend | Vue 3 + TypeScript | typecheck, Vitest, production build | PASS |
| Relational DB, preferably PostgreSQL | PostgreSQL 17 + SQLAlchemy/Alembic | readiness, migration, seed, restart and clean bootstrap | PASS |
| Quick local deployment | Docker Compose + PowerShell scripts | clean-volume `dev.ps1` bootstrap reached healthy backend/frontend/PostgreSQL | PASS |
| Two simultaneously open clients | WebSocket invalidation + REST refetch + fallback refresh | developer manually verified two tabs update automatically on connectivity change | PARTIAL; realtime client foundation PASS, live ranking behavior pending |
| Several POS simulators | Five independent Compose simulator services | five containers ran concurrently and all heartbeats returned `200 OK` | PARTIAL; multi-instance runtime PASS, POS sales generation pending |
| Configurable sales event intensity | Not yet | — | NOT IMPLEMENTED |
| Live ranking | Not yet | — | NOT IMPLEMENTED |
| Last hour / today metrics | Not yet | — | NOT IMPLEMENTED |
| Revenue / sales / average check | Schema foundation only | `pos_events` schema | NOT IMPLEMENTED |
| Leader / outsider / dynamics | Not yet | — | NOT IMPLEMENTED |
| Store detail / top products / plan progress | Seed has products/targets only | schema + seed | NOT IMPLEMENTED |
| Settings | Store fields exist; editing API/UI pending | `stores` schema | PARTIAL |
| Late-arriving events | `occurred_at` and `received_at` schema prepared | migration | NOT IMPLEMENTED |
| Duplicate event protection | `event_id` primary key prepared | migration | PARTIAL; API duplicate/conflict semantics and concurrency proof pending |
| Refunds | SALE/REFUND type and original-event reference prepared | migration | PARTIAL; validation/analytics pending |
| Offline store notification | heartbeat/status foundation only | five heartbeat simulators + connectivity UI | NOT IMPLEMENTED |
| Behind-plan notification | target/timezone fields prepared | store schema | NOT IMPLEMENTED |
| Local midnight per timezone | timezone field prepared | store schema | NOT IMPLEMENTED |
| Restart preserves today's ranking | PostgreSQL persistence foundation verified | five stores survived backend restart; clean DB bootstrap verified | PARTIAL; ranking itself is not implemented, so ranking restart proof is pending |
| Honest state description | Explicit current-state and limitation docs | this file + `PROJECT_STATE.md` | PASS |
| AI prompts / decision log | AI/development docs maintained | `docs/ai/` + `DEVELOPMENT_LOG.md` | PASS for current work |
| Git/time progression | Real repository history starts from verified baseline | commit `a2bf2b7`; push completed; developer confirmed GitHub Actions green | PASS |
