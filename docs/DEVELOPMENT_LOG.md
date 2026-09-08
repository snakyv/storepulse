# Development log

This log must remain truthful. Do not backdate entries or invent commands/results.

## 2026-09-08 — Initial scaffold generation (AI-assisted, pre-local verification)

**Goal:** create a minimal runnable foundation for Mad Devs Case 5 without pretending that unfinished business requirements are complete.

**Work completed:** initial PostgreSQL schema/migration, deterministic seed, FastAPI health/store/heartbeat API, WebSocket invalidation, Vue connectivity dashboard, five heartbeat simulator services, local PowerShell scripts, CI skeleton and project-state documentation.

**AI contribution:** architecture and scaffold source were generated with ChatGPT GPT-5.6 Sol from the developer-approved master engineering brief.

**Developer decisions captured before generation:** Python 3.12, FastAPI, Vue, PostgreSQL, Docker Desktop, Windows/PowerShell workflow; host ports 5432 and 8080 must not be disturbed; project PostgreSQL uses host port 55432.

**Verification:** generation-environment checks recorded in `PROJECT_STATE.md`.

**Result:** checkpoint prepared; local runtime status pending.

**Relevant commit:** none. The archive intentionally contains no fabricated Git history.

---

## 2026-09-08 18:44 +03:00 — First developer-machine runtime validation and Ruff repair

**Goal:** validate the scaffold on the actual Windows + Docker Desktop environment and repair the first failing quality gate.

**Work completed:** Docker Compose built and started PostgreSQL/backend/frontend successfully; migration and deterministic seed executed. The first `verify.ps1` run stopped correctly at Ruff with 19 findings. The revised checkpoint fixes every reported finding. Local verification also compiles the simulator package; GitHub CI additionally runs Ruff against simulator source from the checkout.

**AI contribution:** reviewed the supplied terminal output, mapped each Ruff diagnostic to source, and prepared a corrected checkpoint without disabling the reported rules.

**Developer decisions:** preserve strict Ruff configuration instead of adding blanket ignores; keep the existing port mapping and Docker topology because runtime startup was successful.

**Verification actually executed:** developer-machine Docker build/start/readiness/migration/seed: PASS. Original backend Ruff: FAIL with 19 findings. Generation-environment compile check after repair: PASS. Database-independent Python tests after repair: 5 passed. Revised Docker Ruff/mypy/full pytest/frontend verification: pending developer re-run.

**Result:** PARTIAL PASS — runtime foundation is proven; revised full quality gate still requires re-run.

**Relevant commit:** none; do not create a commit until the revised local verification completes.

---

### Template for the next real work block

```text
## YYYY-MM-DD HH:MM timezone
Goal:
Work completed:
Agent contribution:
Developer decisions:
Verification actually executed:
Result: PASS / FAIL / BLOCKED / NOT TESTED
Relevant commit:
```

---

## 2026-09-08 — Second developer validation: backend gates pass, frontend toolchain incompatibility found

**Goal:** continue the full local quality gate after the pytest path correction.

**Work completed:** the developer rebuilt backend/migrate/seed, started the foundation, then ran the full verification script. Ruff, mypy, backend pytest and simulator compile all passed. Frontend type checking failed before checking project source because `vue-tsc 3.3.11` attempted to load `typescript/lib/tsc` from TypeScript `7.0.2`, which no longer exports that subpath.

**AI contribution:** audited the full supplied project archive and terminal log, verified the TypeScript 7 / vue-tsc incompatibility against upstream Vue language-tools reports, reviewed the remaining scaffold for likely next-gate failures, and prepared checkpoint 00d.

**Developer decisions:** keep `vue-tsc 3.3.11`; pin TypeScript to the known-compatible `6.0.2` rather than disabling type checking. Keep Vite 7.3.6 / Vitest 5.0.0 and pin Node 22.23.2 because both require Node 22.12+ and the developer's Docker environment already ran 22.23.2 successfully.

**Verification actually executed (developer machine):** Docker build/start/migrations/seed: PASS. Ruff: PASS. mypy: PASS. pytest: 6 passed with 2 warnings. Simulator compile: PASS. Frontend typecheck: FAIL at toolchain startup. Frontend unit tests/build: not reached.

**Checkpoint 00d generation checks:** Python compile: PASS. JSON/YAML parse: PASS. configured Python line-length audit: PASS. Full Docker/npm verification: pending developer re-run.

**Result:** PARTIAL PASS — all reached backend/simulator gates are green; frontend dependency compatibility is corrected in source but still requires runtime proof.

**Relevant commit:** none; do not commit until checkpoint 00d verification completes.


---

## 2026-09-08 20:21–20:28 +03:00 — Exact-current audit and asyncio pool/loop correction

**Goal:** stop patching one visible failure at a time, audit the exact developer repository after checkpoint 00d and correct the remaining test-infrastructure defect without weakening production pooling.

**Work completed:** checkpoint 00d was applied twice (the second sync confirmed no source differences), the Git remote was corrected, and a real frontend lockfile was generated under Node 22.23.2 with npm reporting zero vulnerabilities at resolution time. The full verification rebuilt all current images, passed PostgreSQL startup, migration, seed, Ruff and mypy, then backend pytest produced `9 passed / 1 failed`. The failure traceback was traced to the global pooled SQLAlchemy `AsyncEngine` crossing pytest function-scoped asyncio event loops. Checkpoint 00e configures one session loop for async tests/fixtures, adds explicit engine disposal at pytest-session and FastAPI shutdown boundaries, strengthens PostgreSQL readiness waiting, requires the lockfile/`npm ci`, aligns CI runtimes and updates stale documentation.

**AI contribution:** inspected the exact uploaded current project including the real lockfile and complete terminal log, compared the failure with SQLAlchemy async-engine lifecycle semantics and pytest-asyncio loop-scope behavior, then performed repository-wide static checks before preparing the correction.

**Developer decisions:** retain normal SQLAlchemy pooling in the application rather than hiding the test problem with `NullPool`; keep one pooled engine per application event loop; do not commit or push until the full local gate reaches `Verification completed.`

**Verification actually executed (developer machine, before 00e):** lock generation: PASS; npm audit at resolution: 0 vulnerabilities; Docker builds: PASS; PostgreSQL: PASS; migration: PASS; seed: PASS; Ruff: PASS; mypy: PASS; pytest: FAIL (`1 failed, 9 passed`) due cross-loop pooled asyncpg reuse; frontend gates: not reached because verification is fail-fast.

**Checkpoint 00e generation checks:** Python compile: PASS; database-independent tests: 7 passed; JSON/YAML parse: PASS; lock/package metadata consistency: PASS; full Docker/PostgreSQL/frontend runtime: pending developer re-run.

**Result:** PARTIAL PASS — root cause corrected in source; full 00e runtime verification remains required.

**Relevant commit:** none; do not commit until checkpoint 00e verification completes.

---

## 2026-09-08 21:06–21:28 +03:00 — Checkpoint 00e fully verified and foundation published

**Goal:** establish a real, reproducible foundation baseline before starting POS business functionality.

**Work completed:** checkpoint 00e was applied to the local repository and the full verification pipeline completed successfully. The developer then started the application and five heartbeat simulators, verified all five simulator containers running concurrently and receiving successful heartbeat responses, manually confirmed automatic updates in two browser tabs, restarted the backend and confirmed the five seeded stores remained available, deleted the project PostgreSQL volume and successfully bootstrapped from an empty state, and reran the complete verification pipeline after that clean bootstrap.

**AI contribution:** prepared checkpoint 00e, diagnosed the previous cross-event-loop asyncpg test failure, aligned the SQLAlchemy/pytest async lifecycle and helped define the runtime proof sequence. The developer executed and supplied the resulting evidence.

**Developer decisions:** accept checkpoint 00e as the verified foundation only after both the automated quality gate and the manual multi-client/restart/clean-bootstrap scenarios passed; keep PostgreSQL as the source of truth and WebSocket messages as invalidation signals; do not claim sales/ranking/refund requirements before those features exist.

**Verification actually executed:** Docker build: PASS; PostgreSQL readiness: PASS; Alembic migration: PASS; deterministic seed: PASS; Ruff: PASS; mypy: PASS; backend pytest: PASS (`10 passed`); simulator compile: PASS; frontend dependency/version checks: PASS; frontend typecheck: PASS; frontend Vitest: PASS (`2 passed`); frontend production build: PASS; backend readiness/API smoke: PASS; five concurrent heartbeat simulators: PASS; two-tab automatic connectivity refresh: PASS; backend restart persistence for seeded store state: PASS; clean-volume bootstrap: PASS; complete verification rerun after clean bootstrap: PASS.

**Publication:** committed as `a2bf2b7 chore: establish verified StorePulse foundation`, pushed to `origin/main`, with the corresponding GitHub Actions workflow confirmed green by the developer.

**Result:** PASS — checkpoint 00e is the accepted foundation baseline. Remaining Case 5 business requirements continue as separate feature commits.

**Relevant commit:** `a2bf2b7 chore: establish verified StorePulse foundation`.

---

## 2026-09-08 22:25–22:31 +03:00 — Stage 03 idempotent SALE ingestion locally verified

**Goal:** establish the first business write path with PostgreSQL-authoritative idempotency before implementing refunds, simulators or ranking analytics.

**Work completed:** added `POST /api/v1/events` for SALE events; strict request validation; exact-duplicate `200` semantics; conflicting same-`event_id` `409`; PostgreSQL `INSERT ... ON CONFLICT DO NOTHING` authority; unknown reference handling; independent `occurred_at`/`received_at`; accepted-sale connectivity update; `events.changed` invalidation; PostgreSQL cleanup-aware integration tests; concurrent identical/conflicting request tests; Stage 03 architecture/contract documentation; and an actual HTTP accepted/duplicate/conflict smoke scenario in GitHub Actions.

**AI contribution:** designed and implemented the Stage 03 candidate, kept PostgreSQL as the idempotency authority, isolated test data from demo state, documented deferred refund behavior explicitly and prepared concurrency tests that exercise the real database path.

**Developer decisions:** keep the existing published initial migration unchanged because the required `pos_events` identity/timestamp columns already exist; do not implement half-safe refunds in the SALE stage; preserve REST as authoritative state and use WebSocket only for invalidation; do not start Stage 04 until this feature commit is pushed and its GitHub Actions run is green.

**Verification actually executed on the developer machine:** Stage 03 synchronization: PASS; `git diff --check`: PASS; Docker image build: PASS; PostgreSQL readiness: PASS; Alembic migration: PASS; deterministic seed: PASS; Ruff: PASS; mypy: PASS (`10 source files`); backend pytest: PASS (`25 passed`); simulator compile: PASS; frontend dependency/version checks: PASS; frontend typecheck: PASS; frontend Vitest: PASS (`2 passed`); frontend production build: PASS; backend readiness: PASS; seeded stores API smoke: PASS (exactly five stores); full `scripts/verify.ps1`: PASS.

**Publication status:** local feature gate PASS. GitHub Actions for this Stage 03 commit is not claimed until the commit is pushed and the workflow actually completes.

**Result:** PASS for the local Stage 03 gate — ready to commit as the isolated SALE-ingestion feature.

**Relevant commit:** planned `feat(events): add idempotent POS sale ingestion`; exact commit SHA is intentionally not invented before commit creation.
