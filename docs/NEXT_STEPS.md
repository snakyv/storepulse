# Delivery roadmap

Verified public work through Stage 04 is complete. Stage 05 now has a clean local end-to-end PASS: repository-wide Ruff, backend mypy/pytest, simulator tests, frontend checks, the five-producer traffic contract, duplicate persistence proof, deterministic cleanup, backend restart readiness, post-restart run isolation and store-state restoration all passed. The only remaining Stage 05 gate is publication: amend the existing feature commit with the verified candidate, push with `--force-with-lease`, and require the resulting GitHub Actions run to be green.

## Stage 05 — local PASS, GitHub Actions rerun pending

Planned commit message (unchanged):

```text
feat(simulator): generate resilient configurable POS traffic
```

Final local evidence on 2026-09-09:

```text
Project Ruff                         PASS
Backend mypy                         PASS
Backend pytest                       47 passed
Simulator unit tests                 9 passed
Verification helper tests            16 passed
Frontend typecheck/Vitest/build      PASS
Five producer stores                 PASS
SALE rows                            20
REFUND rows                          19
Late rows                            39
Exact duplicate replay               PASS
Duplicate durable row count          1
Backend write barrier                PASS
Verification data cleanup            PASS
Backend restart readiness            PASS
Post-restart run isolation           PASS
Store connectivity restore           PASS
Verification completed               PASS
```

Immediate action: review the staged diff, amend the existing Stage 05 feature commit without changing its message, push with `--force-with-lease`, and wait for GitHub Actions. Do not start analytics until that workflow is green.

## Remaining isolated commits

```text
feat(analytics): add timezone-aware store rankings
feat(stores): add store insights and persisted settings
feat(ui): build realtime ranking and store management dashboard
feat(alerts): add durable offline incident notifications
feat(alerts): add local-noon plan monitoring
test: prove concurrency realtime timezone and restart behavior
docs: finalize submission evidence and demo guide
```

## Delivery discipline

Every stage follows:

```text
implement
→ static audit
→ Ruff/mypy/typecheck
→ unit + integration tests
→ Docker verification
→ manual scenario when required
→ git diff review
→ commit
→ push
→ GitHub Actions green
→ next stage
```

Do not add Kafka, Redis, authentication or cloud infrastructure before mandatory Case 5 behavior is implemented and proven.
