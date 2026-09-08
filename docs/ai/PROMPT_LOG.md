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
