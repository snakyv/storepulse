# Next steps

Implement in this order so each step can be tested before the next:

1. POS SALE ingestion with database-enforced idempotency and conflicting-payload `409` behavior.
2. REFUND validation, including partial/full/over-refund cases.
3. Simulator sales, duplicate, late-batch, refund and burst modes.
4. Ranking analytics for rolling last hour and per-store local "today".
5. Store detail time-series and top-products aggregation.
6. Persisted settings editing.
7. Offline incident lifecycle + transactional notification outbox + mock mailbox.
8. Local-noon behind-plan evaluation with one notification per store/local date.
9. Concurrency, five-producer, two-tab, timezone and restart proofs.
10. Final README/demo, frontend lint decision, CI hardening and clean-room audit.

Do not add Kafka, Redis, authentication or deployment infrastructure before the mandatory behavior above is correct and proven.
