from datetime import UTC, datetime, timedelta


def is_store_online(
    last_seen_at: datetime | None,
    *,
    now: datetime | None = None,
    threshold_seconds: int = 30,
) -> bool:
    if threshold_seconds <= 0:
        raise ValueError("threshold_seconds must be positive")

    if last_seen_at is None:
        return False

    reference = now or datetime.now(UTC)
    if last_seen_at.tzinfo is None:
        raise ValueError("last_seen_at must be timezone-aware")
    if reference.tzinfo is None:
        raise ValueError("now must be timezone-aware")

    return reference - last_seen_at <= timedelta(seconds=threshold_seconds)
