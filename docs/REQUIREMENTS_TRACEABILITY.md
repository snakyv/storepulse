# Requirements traceability

Status vocabulary: `PASS`, `PARTIAL`, `NOT IMPLEMENTED`, `NOT TESTED`.

| Employer requirement | Current implementation | Proof in scaffold | Status |
|---|---|---|---|
| Separate backend and frontend communicating over network | FastAPI + Vue over HTTP/WebSocket | Docker Compose + local runtime startup | PASS for scaffold runtime |
| Python backend | Python 3.12 / FastAPI | `backend/` | PASS |
| Vue or React frontend | Vue 3 + TypeScript | `frontend/` | PASS |
| Relational DB, preferably PostgreSQL | PostgreSQL 17 + SQLAlchemy/Alembic | migration + successful local container startup | PASS for scaffold runtime |
| Quick local deployment | Docker Compose + PowerShell scripts | `scripts/dev.ps1`; developer-machine run reached ready state | PASS for scaffold |
| Two simultaneously open clients | WebSocket invalidation + REST refetch | frontend socket logic | PARTIAL; two-tab proof still required |
| Several POS simulators | Five Compose simulator services | `docker-compose.yml` | PARTIAL; heartbeat only, five-service runtime still to verify |
| Configurable sales event intensity | Not yet | — | NOT IMPLEMENTED |
| Live ranking | Not yet | — | NOT IMPLEMENTED |
| Last hour / today metrics | Not yet | — | NOT IMPLEMENTED |
| Revenue / sales / average check | Schema foundation only | `pos_events` schema | NOT IMPLEMENTED |
| Leader / outsider / dynamics | Not yet | — | NOT IMPLEMENTED |
| Store detail / top products / plan progress | Seed has products/targets only | schema + seed | NOT IMPLEMENTED |
| Settings | Store fields exist; editing API/UI pending | `stores` schema | PARTIAL |
| Late-arriving events | `occurred_at` and `received_at` schema prepared | migration | NOT IMPLEMENTED |
| Duplicate event protection | `event_id` primary key prepared | migration | PARTIAL; API semantics/tests pending |
| Refunds | SALE/REFUND type and original event FK prepared | migration | PARTIAL; validation/analytics pending |
| Offline store notification | heartbeat/status foundation only | heartbeat endpoint | NOT IMPLEMENTED |
| Behind-plan notification | target/timezone fields prepared | store schema | NOT IMPLEMENTED |
| Local midnight per timezone | timezone field prepared | store schema | NOT IMPLEMENTED |
| Persistence after restart | PostgreSQL volume configured | Compose | NOT TESTED with restart scenario |
| Honest state description | Explicit docs | this file + `PROJECT_STATE.md` | PASS |
| AI prompts / decision log | Initial AI/development docs | `docs/ai/` | PASS for checkpoint |
| Git/time progression | No fabricated history included | README + development log | Ready to begin after revised quality gate passes |
