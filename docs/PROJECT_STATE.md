# Project state

## Current checkpoint

Stage 04 safe REFUND processing has been locally verified, committed, pushed and confirmed green in GitHub Actions by the developer. **Stage 05 — resilient configurable POS traffic** now has a clean end-to-end local PASS, including repository-wide quality gates, five-producer business evidence, deterministic verification cleanup and backend state restoration.

Stage 05 is **LOCAL END-TO-END PASS / GITHUB ACTIONS RERUN PENDING**. The first published candidate exposed a CI-only repository-wide Ruff formatting failure. The hardening work subsequently centralized Ruff targets and simulator smoke/cleanup into shared cross-platform Python entrypoints used by both local verification and GitHub Actions. The final local run completed all gates successfully; the remaining publication step is to amend the existing Stage 05 commit and require the resulting GitHub Actions run to be green.

## Verified through Stage 04

- Separate FastAPI/Vue services with PostgreSQL persistence and Docker Compose.
- Deterministic five-store / ten-product seed.
- WebSocket invalidation with REST refetch.
- Idempotent `SALE` ingestion with PostgreSQL `event_id` authority.
- Discriminated `SALE` / `REFUND` body on `POST /api/v1/events`.
- Refund requires `original_event_id`.
- Referenced original must exist and be a top-level SALE.
- Refund store and product must match the original sale.
- Cumulative refunded quantity cannot exceed sale quantity.
- Cumulative refunded amount cannot exceed sale amount.
- Refund decisions for the same original sale are serialized with `SELECT ... FOR UPDATE`.
- Exact REFUND replay returns `200 duplicate`; conflicting reuse of its `event_id` returns `409`.
- Late SALE/REFUND timestamps preserve producer `occurred_at` independently from `received_at`.
- Migration `20260908_0002_refund_invariants.py` adds database reference-shape constraints.
- Developer-machine Stage 04 verification passed with `47 passed` backend tests and all existing frontend/build/API-smoke gates.
- The developer confirmed the Stage 04 GitHub Actions run green after publication.

## Stage 05 candidate scope

- five real POS producers instead of heartbeat-only containers;
- per-store configurable `EVENTS_PER_SECOND`;
- valid SALE traffic using seeded SKUs and integer-cents totals;
- safe REFUND generation only against producer-acknowledged sales;
- local refund-capacity reservation before queueing;
- exact duplicate replay with the same payload/event ID;
- late `occurred_at` generation;
- retryable transport classification;
- retry with the same immutable payload;
- exponential backoff with jitter;
- bounded queue/backpressure instead of silent event dropping;
- independent heartbeat loop;
- distinct `source_instance` identity per container;
- simulator unit tests;
- five-container PostgreSQL traffic smoke in local verification and GitHub Actions.

## Stage 05 verification status

Final developer-machine full gate on 2026-09-09:

- Compose validation/build: PASS;
- PostgreSQL readiness, migrations and deterministic seed: PASS;
- repository-wide Ruff: PASS;
- backend mypy: PASS (`10 source files`);
- backend pytest: PASS (`47 passed`);
- simulator compile: PASS;
- simulator unit tests: PASS (`9 passed`);
- shared verification-helper tests: PASS (`16 passed`);
- frontend typecheck/Vitest/build: PASS (`2` Vitest tests);
- backend readiness and seeded five-store API smoke: PASS;
- POS traffic observed from exactly five stores: PASS;
- isolated verification run: `verify-dd56b81aafad`;
- verification-run durable traffic: `20` SALE, `19` REFUND, `39` late rows;
- exact duplicate replay observed: PASS;
- replayed `event_id` durable row count: `1`;
- backend write barrier: PASS;
- simulator verification-data cleanup: PASS;
- backend restart readiness: PASS;
- post-restart run isolation: PASS;
- store connectivity restore: PASS;
- final `Verification completed.`: PASS.

The first published Stage 05 candidate's GitHub Actions run was not green because CI caught repository-wide Ruff import-order findings that the older local gate did not cover. That parity defect and the later cleanup-harness defects have been structurally corrected. Local and CI now share `scripts/run_ruff.py` and `scripts/verify_simulator_smoke.py`. Stage 05 is locally verified; one amended push and one green GitHub Actions run remain before public completion is claimed.

## Still incomplete after the Stage 05 candidate

- ranking by revenue, effective sales count and average check;
- refunds decreasing ranking metrics;
- rolling last-hour and per-store local-day windows;
- leader/outsider and dynamics;
- store detail analytics and persisted settings;
- offline incident lifecycle and notification outbox;
- local-noon behind-plan alerts;
- final measured five-producer no-loss/load proof;
- automated Playwright two-client ranking proof;
- restart proof for today's ranking.

## Next commit after Stage 05

Once the existing Stage 05 commit is amended with the locally verified candidate and GitHub Actions is green:

```text
feat(analytics): add timezone-aware store rankings
```
