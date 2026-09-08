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

---

## 2026-09-08 — Stage 04 safe refund processing candidate prepared

**Goal:** add refund behavior as an isolated feature stage without weakening the Stage 03 event-idempotency contract.

**Work completed in the candidate:** introduced a discriminated SALE/REFUND request contract; required `original_event_id` for REFUND; added original-sale existence/type validation; same-store and same-product checks; independent cumulative quantity/amount limits; per-original `SELECT ... FOR UPDATE` serialization; a post-lock event-ID recheck for concurrent exact retries; PostgreSQL check constraints for original-reference shape/self-reference; refund schema, integration, database-constraint and concurrency tests; refund contract documentation; and an expanded GitHub Docker smoke scenario for accepted/duplicate/over-limit refunds.

**Concurrency decision:** cumulative refund limits are protected by the database row lock on the referenced SALE, not by an in-process mutex. This keeps the invariant correct across concurrent requests and future multi-process deployment. The event-ID primary key remains the separate authority for idempotency.

**Migration decision:** the published initial migration is not rewritten. Stage 04 adds `20260908_0002_refund_invariants.py`, preserving real migration history.

**Verification executed in the artifact-generation environment:** Python compile: PASS; database-independent pytest: PASS (`16 passed`, integration tests deselected); FastAPI OpenAPI generation: PASS; SALE/REFUND discriminator visible: PASS. Full pinned Docker Ruff/mypy/PostgreSQL integration/frontend verification is intentionally **NOT TESTED** here and remains the developer-machine gate before commit.

**Result:** candidate prepared; do not mark Stage 04 complete or commit until `scripts/verify.ps1` passes on the developer machine.

**Relevant commit:** planned `feat(refunds): enforce safe refund processing`; exact SHA does not exist yet.

---

## 2026-09-09 — Stage 04 safe refund processing locally verified

**Goal:** prove the refund transaction model and cumulative-limit concurrency safeguards in the real pinned Docker/PostgreSQL environment before creating the isolated feature commit.

**Work completed:** applied the Stage 04 candidate, upgraded the existing database from migration `20260908_0001` to `20260908_0002`, and ran the complete repository verification pipeline. The verified feature includes discriminated REFUND ingestion, original-SALE validation, same-store/product enforcement, independent cumulative quantity/amount limits, per-original `SELECT ... FOR UPDATE` serialization, post-lock idempotency re-checking, database reference-shape constraints and refund concurrency tests.

**AI contribution:** designed and prepared the Stage 04 implementation/tests/documentation and reviewed the developer-supplied verification output.

**Developer decisions:** preserve the published initial migration and add a new migration; use PostgreSQL row locking rather than process-local mutexes; keep ranking effects out of this commit; do not claim GitHub Actions before the feature is actually pushed.

**Verification actually executed on the developer machine:** Stage 04 synchronization: PASS; `git diff --check`: PASS; Docker image build: PASS; PostgreSQL readiness: PASS; Alembic upgrade `20260908_0001 -> 20260908_0002`: PASS; deterministic seed: PASS; Ruff: PASS; mypy: PASS (`10 source files`); backend pytest: PASS (`47 passed`); simulator compile: PASS; frontend dependency/version checks: PASS; frontend typecheck: PASS; frontend Vitest: PASS (`2 passed`); frontend production build: PASS; backend readiness: PASS; seeded-store API smoke: PASS (exactly five stores); complete `scripts/verify.ps1`: PASS.

**Publication status:** local Stage 04 gate PASS. GitHub Actions for the Stage 04 feature commit remain NOT TESTED until the commit is pushed.

**Result:** PASS for the local Stage 04 gate — ready to commit as `feat(refunds): enforce safe refund processing`.

**Relevant commit:** planned `feat(refunds): enforce safe refund processing`; exact SHA is intentionally not invented before Git creates it.

---

## 2026-09-09 — Stage 04 publication confirmed; Stage 05 POS simulator candidate prepared

**Goal:** replace the heartbeat-only demo with five real POS producers while preserving the already verified backend event semantics and keeping the simulator stage isolated from ranking analytics.

**Prior-stage publication:** the developer confirmed that `feat(refunds): enforce safe refund processing` was committed, pushed, and its GitHub Actions workflow completed successfully. The exact commit SHA was not supplied to this artifact-generation environment, so it is not invented here.

**Work completed in the Stage 05 candidate:** replaced the monolithic heartbeat loop with a structured simulator runtime; added per-store configurable Poisson event intensity; deterministic seeded product selection; integer-cents SALE payloads; producer-local acknowledged-sale ledger; REFUND generation with pre-queue capacity reservation; exact duplicate replays; late `occurred_at`; retryable HTTP classification; same-event retry after ambiguous failures; capped exponential backoff with jitter; bounded outbound queue/backpressure; independent heartbeat and stats loops; per-container source identity; simulator unit tests; five-container business-traffic smoke checks for local verification and GitHub Actions; and frontend invalidation coalescing so sustained POS traffic cannot indefinitely postpone refreshes or create overlapping REST calls.

**Reliability decision:** network/server retries never create a new event ID or mutate the payload. This intentionally composes with the Stage 03/04 backend idempotency contract: if a request committed but its response was lost, the replay should resolve as an exact duplicate. The producer defaults to unlimited retry attempts for retryable errors and lets the bounded queue apply backpressure rather than silently discarding generated events.

**Refund decision:** the producer only refunds SALE events that this process has already received an accepted/duplicate success for. Refund capacity is reserved before queueing so multiple local workers cannot overbook one sale. PostgreSQL remains authoritative; producer state is only a pre-validation convenience.

**Duplicate decision:** deliberate duplicate replays are sent directly by the delivery worker after the original event succeeds. They are not put back into the bounded queue, avoiding a queue-full deadlock where all consumers could block trying to enqueue duplicate work.

**Scope boundary:** the simulator ledger/queue are process-local. A hard producer-process crash can lose generated-but-unacknowledged work. Stage 05 targets network/backend resilience and realistic assignment traffic; the final measured no-loss/load proof remains a later test stage. No durable simulator outbox, Kafka or Redis is introduced without evidence that the assignment requires it.

**Verification in artifact-generation environment:** Python compile PASS; simulator unit tests PASS (`9 passed`); existing database-independent backend pytest PASS (`16 passed`, `31 deselected`); Docker Compose YAML parse PASS; GitHub Actions YAML parse PASS; extracted simulator-smoke Bash syntax PASS; Python 100-character audit PASS; trailing-whitespace audit PASS. Full Docker/PostgreSQL five-producer runtime, frontend typecheck/build after the coalescing change, and complete `scripts/verify.ps1` remain **NOT TESTED** until the developer executes them.

**Result:** candidate prepared; do not commit until the complete local Stage 05 gate reaches `Verification completed.`

**Relevant commit:** planned `feat(simulator): generate resilient configurable POS traffic`; exact SHA does not exist yet.

## 2026-09-09 — Stage 05 Windows smoke-harness defects diagnosed and hardened

**Context:** two local Stage 05 verification attempts reached the five-simulator smoke after
all earlier gates had passed. The first attempt was interrupted by Windows PowerShell
treating normal Docker cleanup stderr as a terminating `NativeCommandError`. The cleanup
path was corrected so it cannot mask the primary smoke result.

**Second-attempt diagnosis:** the next run again passed backend Ruff, mypy, all 47 backend
tests, all 9 simulator unit tests, frontend typecheck/Vitest/build, backend readiness and
the five-store API smoke. It also advanced past the durable five-store/SALE/REFUND/late
database checks before failing the duplicate-log assertion. The failure was a verifier
false negative, not a producer duplicate failure: in Windows PowerShell 5.1,
`$logs -notmatch <pattern>` applied to a string array returns every non-matching element
rather than one Boolean. Because simulator logs necessarily contain many unrelated lines,
the resulting non-empty collection is truthy even when another line contains the required
duplicate evidence.

**Hardening applied:** simulator logs are now joined into one scalar before regex matching;
each local smoke receives a unique verification run tag; only simulator containers are
force-recreated with `--no-deps` so their logs are fresh; fixed sleeps were replaced by a
bounded polling window; a duplicate log event ID is cross-checked to have exactly one
durable database row; verification cleanup is scoped to the unique run tag; and original
store `last_seen_at` values are snapshotted and restored. GitHub's simulator smoke was
hardened to use the same bounded-polling and one-durable-row proof.

**Result:** verifier defects are corrected in the candidate. Full Stage 05 remains
**NOT YET COMPLETE** until the corrected local `scripts/verify.ps1` reaches
`Verification completed.` and the eventual feature commit receives a green GitHub Actions
run.

## 2026-09-09 — Stage 05 corrected local verification PASS

**Verification actually executed (developer machine):** the hardened Stage 05c verifier
completed end-to-end in the pinned Windows/Docker/PostgreSQL environment. Compose
validation/build, PostgreSQL readiness/migrations/seed, Ruff, mypy, all `47` backend tests,
simulator compile, all `9` simulator unit tests, frontend typecheck, `2` Vitest tests,
production build, backend readiness and the seeded five-store API smoke all passed.

**Five-producer evidence:** the isolated run `verify-cec2702c66ce` observed durable POS
traffic from exactly five stores with `46` SALE rows, `52` REFUND rows and `98` late rows.
The verifier observed an exact duplicate replay and independently confirmed that the
replayed `event_id` still had exactly `1` durable PostgreSQL row. The script ended with
`Verification completed.`

**Result:** Stage 05 is **LOCAL PASS**. The feature is ready for the isolated commit
`feat(simulator): generate resilient configurable POS traffic`. GitHub Actions for that
commit remains **NOT TESTED** until push; do not claim Stage 05 public completion until the
workflow is green.


## 2026-09-09 — Stage 05 CI/local quality-gate parity root-cause and structural fix

**Evidence reviewed:** the full current repository, the exported GitHub Actions logs for
the first published Stage 05 candidate, and the subsequent Windows PowerShell attempts to
reproduce the CI Ruff scope locally.

**Root-cause chain:** the published commit's backend job failed on three Ruff `I001`
findings in simulator test import blocks. The earlier local verifier had linted only
`backend/app` and `backend/tests`, so it could not detect those findings. The first parity
patch reused CI-relative paths inside the backend image, but that image intentionally does
not contain sibling `simulator/` sources, producing `E902` path errors. The next patch
mounted the repository read-only so the paths existed, but Ruff then attempted to create
`backend/.ruff_cache` and failed on the read-only filesystem.

**Structural correction:** do not keep separate shell-specific Ruff target lists.
`scripts/run_ruff.py` is now the single cross-platform Ruff entrypoint. It resolves the
repository root itself, validates every expected target, uses the explicit
`backend/pyproject.toml` configuration, includes backend + simulator source/tests plus the
runner itself, and invokes Ruff with `--no-cache`. Local PowerShell runs this exact script
inside the pinned backend image with the repository mounted read-only; GitHub Actions runs
the same script from the checked-out repository. This removes both path-layout assumptions
and cache-write requirements from lint parity.

**CI hardening:** GitHub Actions are moved to current Node-24-based generations and pinned
by immutable commit SHA, workflow permissions are explicitly read-only, and each job has a
bounded timeout. The simulator/business smoke semantics are unchanged.

**Result:** source-level correction prepared. Artifact-generation checks pass, but Docker
PowerShell verification and the amended GitHub Actions run remain **NOT TESTED** until the
developer executes them. Do not claim Stage 05 public completion before both are green.

## 2026-09-09 — Stage 05 cleanup failure isolated; simulator verification unified cross-platform

**Evidence reviewed:** the complete latest Windows `verify.ps1` transcript and the full current Stage 05 repository candidate.

**Latest run result:** repository-wide Ruff PASS; backend mypy PASS; backend pytest PASS (`47 passed`); simulator compile PASS; simulator unit tests PASS (`9 passed`); frontend typecheck/Vitest/build PASS; backend readiness PASS; seeded five-store API smoke PASS. The five-producer contract also passed with exactly five stores, `61` SALE rows, `72` REFUND rows, `133` late rows, an observed exact duplicate replay and exactly one durable PostgreSQL row for that replayed event ID.

**Failure point:** only the post-smoke cleanup failed. The legacy PowerShell implementation combined REFUND deletion, SALE deletion and store-state restore into one `psql -c` call and redirected all native output to null. Because PostgreSQL stderr was discarded, the exact SQL sub-error is not recoverable from the supplied transcript. No business/runtime failure is inferred from that missing evidence.

**Windows PowerShell portability hazard identified:** the legacy cleanup also parsed a top-level JSON array with `ConvertFrom-Json` and then depended on normal pipeline enumeration. Windows PowerShell 5.1 treats top-level JSON arrays differently from ordinary pipeline collections, so that snapshot/restore path was unnecessarily shell-version-sensitive even apart from the swallowed PostgreSQL stderr. The replacement Python harness parses and validates the JSON structure directly and sends typed JSON records back to PostgreSQL.

**Structural correction:** simulator smoke verification is moved into `scripts/verify_simulator_smoke.py`, a stdlib-only cross-platform runner invoked unchanged from local PowerShell verification and GitHub Actions. It owns unique run-tag creation, deterministic simulator environment, bounded polling, durable SALE/REFUND/late evidence, duplicate-event persistence proof, simulator stop, atomic FK-safe REFUND-before-SALE cleanup, zero-row cleanup verification, typed JSON `last_seen_at`/`updated_at` store-state restore and restore verification. Every Docker/psql subprocess captures stdout/stderr and reports the exact failing command instead of swallowing diagnostics.

**Regression protection:** added `scripts/tests/test_verify_simulator_smoke.py`; the repository-wide Ruff contract now also covers the shared smoke runner and its tests; both local verification and CI execute the helper unit tests. The Docker-smoke job now invokes the same Python smoke runner instead of maintaining a separate Bash implementation.

**Status:** Stage 05 business/runtime behavior remains PASS. The amended candidate still requires one clean full local run ending in `Verification completed.` and one green GitHub Actions run before Stage 05 is declared publicly verified.

## 2026-09-09 — Stage 05 shared verifier write-barrier correction

**Evidence reviewed:** after the shared Python smoke harness was introduced, a full local run passed repository-wide Ruff, backend/simulator/frontend checks and the complete five-producer evidence contract, then failed because the run-tag row count did not become quiescent quickly enough after producer stop.

**Root cause:** producer termination alone did not prove that requests already accepted by the backend had finished their database transactions. Waiting for several stable row-count reads remained a timing heuristic and could fail under legitimate in-flight backend work.

**Structural correction:** replace quiescence polling with a deterministic write barrier. The verifier now confirms all simulator services are stopped (with kill fallback), stops and verifies the backend before cleanup, performs FK-safe transactional cleanup and store-state restoration while no application writer can commit, restarts the backend, waits for readiness, then verifies no verification rows reappear and store timestamps still match the pre-smoke snapshot. Helper regression coverage increased to `16` tests.

## 2026-09-09 — Stage 05 final local end-to-end PASS

**Verification actually executed on the developer machine:** `git diff --check` PASS; repository-wide Ruff PASS; backend mypy PASS; backend pytest PASS (`47 passed`); simulator compile PASS; simulator unit tests PASS (`9 passed`); shared verification-helper tests PASS (`16 passed`); frontend typecheck PASS; frontend Vitest PASS (`2 passed`); frontend production build PASS; backend readiness PASS; seeded five-store API smoke PASS.

**Five-producer evidence:** isolated run `verify-dd56b81aafad` observed durable traffic from exactly five stores with `20` SALE rows, `19` REFUND rows and `39` late rows. Exact duplicate replay was observed and the replayed `event_id` had exactly `1` durable PostgreSQL row.

**Lifecycle/cleanup evidence:** backend write barrier PASS; simulator verification-data cleanup PASS; backend restart readiness PASS; post-restart run isolation PASS; store connectivity restore PASS. The script ended with `Verification completed.`

**Result:** Stage 05 is **LOCAL END-TO-END PASS**. No additional application/simulator business-logic changes are required from this evidence. The remaining publication gate is to amend the existing `feat(simulator): generate resilient configurable POS traffic` commit, push with `--force-with-lease`, and require the resulting GitHub Actions workflow to be green before starting Stage 06 analytics.
