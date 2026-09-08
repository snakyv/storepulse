# Prompt / decision log

## 2026-09-08 — Master engineering brief

The developer supplied a detailed master prompt for Mad Devs Junior Agentic Developer Case 5 (StorePulse). It defines the final target: FastAPI/Python 3.12, Vue, PostgreSQL, realtime updates, event idempotency, late events, refunds, five simulators, timezone-aware daily logic, notifications, tests, Docker, CI and truthful AI/development logs.

The full master prompt remains in the ChatGPT conversation/export. This repository records decisions and implementation outcomes rather than fabricating a copied session export.

## 2026-09-08 — Scaffold request

Developer instruction: create the first complete project skeleton, include necessary local and GitHub testing files, avoid unnecessary files, package it as an archive, then continue improving from this verified base.

Decision: implement one real vertical foundation slice (PostgreSQL + heartbeat + WebSocket + Vue) while leaving unfinished assignment behavior explicitly marked as not implemented.

## 2026-09-08 18:44 +03:00 — Runtime validation follow-up

**Input:** developer supplied the complete first `dev.ps1` / `verify.ps1` terminal log.

**Outcome:** Docker startup, PostgreSQL health, migrations, seed and backend readiness were accepted as real evidence. Ruff reported 19 concrete findings; the checkpoint was revised to fix them without weakening lint rules. Full verification remains pending re-run.


## 2026-09-08 — Full scaffold audit after frontend typecheck failure

Developer supplied the current `StorePulse.zip` and the complete local verification output. The audit traced the failure to TypeScript 7.0.2 incompatibility with vue-tsc 3.3.11, then reviewed Docker/CI version alignment, test warnings, stale-image risk, WebSocket reconnection behavior, time-derived connectivity refresh and configuration validation. Checkpoint 00d pins a compatible TypeScript version and hardens the verification path without weakening any quality gate.


## 2026-09-08 — Exact-current repository audit after 00d pytest failure

Developer supplied the exact current StorePulse repository including the newly generated `frontend/package-lock.json` and the complete 00d verification output. The failure was not the expected `404`; it was pooled asyncpg state crossing pytest's default function-scoped event loops. The correction keeps production pooling, aligns async test loop lifetime with the application process, adds explicit pool disposal, strengthens verification startup ordering, requires deterministic `npm ci`, and updates CI/documentation to match the actual repository state.

## 2026-09-08 — Stage 03 idempotent SALE ingestion

Developer instruction: proceed after the verified baseline and implement the next isolated feature commit, `feat(events): add idempotent POS sale ingestion`, with PostgreSQL-enforced idempotency, exact duplicate handling, conflicting duplicate `409`, late `occurred_at` preservation and concurrency tests.

Decision: keep PostgreSQL as the sole event authority and use `INSERT ... ON CONFLICT DO NOTHING` against the existing `event_id` primary key. Do not add Redis/Kafka or in-memory deduplication. Stage 03 accepts only validated SALE events; REFUND remains explicitly rejected until the dedicated refund-safety stage.

## 2026-09-08 — Stage 04 safe refund processing

Developer instruction: proceed with the next isolated commit, `feat(refunds): enforce safe refund processing`, implementing partial/full refunds, original-sale validation, cumulative limits and concurrency-safe over-refund protection as professionally as planned.

Decision: model a refund as a separate immutable POS event referencing the original SALE. Serialize cumulative-limit decisions with PostgreSQL `SELECT ... FOR UPDATE` on that sale, re-check the refund event ID after any lock wait, keep primary-key/`ON CONFLICT` idempotency, add a new migration for database row-shape invariants, and defer ranking subtraction to the analytics stage rather than mixing aggregation into ingestion.

## 2026-09-09 — Stage 05 resilient POS traffic

Developer instruction: proceed after the verified/published safe-refund stage with the next isolated commit, `feat(simulator): generate resilient configurable POS traffic`, replacing heartbeat-only containers with five genuine POS producers and implementing configurable intensity, SALE/REFUND traffic, retry-safe duplicate behavior, late events and preparation for later five-producer load proof.

Decision: keep the simulator as a lightweight Python/httpx process rather than introducing a broker. Use per-store environment-configured Poisson rates, a bounded in-memory queue with backpressure, same-payload retries with exponential backoff/jitter, producer-local acknowledged-sale state for valid refunds, and deliberate exact duplicate replays. Preserve PostgreSQL/backend idempotency as the authoritative correctness boundary. Add unit tests plus an actual five-container smoke before claiming the feature complete.

## 2026-09-09 — Stage 05 verification-harness diagnosis

Developer supplied the complete current repository plus the full repeated Windows
PowerShell verification log and asked for a professional root-cause analysis and repair.

Diagnosis: the simulator business path had already passed all unit and pre-smoke quality
gates. The repeated duplicate-smoke failure came from Windows PowerShell collection
semantics: native `docker compose logs` output is an array of lines, so applying
`-notmatch` directly returns all non-matching lines rather than one Boolean. A non-empty
result therefore triggered a false failure even if another log line contained the expected
duplicate evidence.

Decision: harden the smoke rather than weaken it. Join logs to a scalar before regex
matching, isolate every run with a unique tag and fresh simulator containers, poll with a
bounded timeout instead of sleeping a fixed duration, verify the replayed event ID has
exactly one durable row, preserve/restore store connectivity timestamps, and apply the
same stronger polling/one-row evidence model in GitHub Actions. Stage 05 remains
uncommitted until the corrected full local gate passes.

## 2026-09-09 — Stage 05 corrected verification result

Developer supplied the complete corrected `scripts/verify.ps1` output. The final run passed
all quality, backend, simulator, frontend and Docker gates, then observed traffic from
exactly five stores with 46 SALE rows, 52 REFUND rows and 98 late rows. It also observed an
exact duplicate replay and confirmed one durable database row for the replayed event ID.
The run ended with `Verification completed.`. Documentation was synchronized to mark Stage
05 LOCAL PASS while leaving the post-push GitHub Actions gate explicitly unverified.


## 2026-09-09 — Stage 05 CI parity hardening

Developer supplied the full current project, GitHub Actions logs and local PowerShell
failures and requested a repository-wide root-cause analysis rather than another narrow
patch. The analysis separated three issues: the original CI-only Ruff scope gap, invalid
CI-relative simulator paths inside the local backend image, and Ruff cache writes against
a read-only bind mount.

Decision: replace duplicated Ruff command lines with one cross-platform
`scripts/run_ruff.py` contract, run it in both local verification and CI, make it
configuration-explicit and cache-free, retain a read-only local repository mount, and pin
current Node-24 GitHub Actions by immutable SHA. Runtime simulator logic is intentionally
unchanged because the evidence did not identify a business-path defect.

## 2026-09-09 — Stage 05 shared smoke/cleanup harness hardening

User supplied the latest full local verification transcript after prior CI-parity fixes and requested a thorough root-cause analysis plus a durable correction. AI reviewed the exact failure sequence, preserved the already-passing simulator/backend business logic, replaced duplicated PowerShell/Bash simulator smoke implementations with one stdlib Python harness, added cleanup/state-restore diagnostics and helper tests, and kept the stage unverified until a new local and GitHub Actions run actually pass.

## 2026-09-09 — Stage 05 deterministic cleanup barrier and final local proof

User supplied repeated full Windows verification output and requested root-cause-first hardening without changing already-passing business logic. The remaining cleanup race was traced to using producer stop plus row-count quiescence as a proxy for completion of backend transactions. The verifier was changed to establish a deterministic backend write barrier before transactional cleanup, restart the backend afterward, and verify post-restart isolation plus restored store state. Regression helper coverage increased to 16 tests.

The developer then supplied a full successful run: repository-wide Ruff PASS, backend mypy PASS, 47 backend tests PASS, 9 simulator tests PASS, 16 verification-helper tests PASS, frontend checks PASS, five-store producer smoke PASS with 20 SALE, 19 REFUND and 39 late rows, exact duplicate persistence proof PASS, cleanup/lifecycle restoration PASS, and final `Verification completed.`. Stage 05 is now local end-to-end PASS; GitHub Actions for the amended commit remains the final publication gate.
