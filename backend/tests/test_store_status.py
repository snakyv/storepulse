from datetime import UTC, datetime, timedelta

import pytest

from app.services import is_store_online


def test_store_without_heartbeat_is_offline() -> None:
    assert is_store_online(None, threshold_seconds=30) is False


def test_recent_heartbeat_is_online() -> None:
    now = datetime(2026, 9, 8, 12, 0, tzinfo=UTC)
    last_seen = now - timedelta(seconds=29)
    assert is_store_online(last_seen, now=now, threshold_seconds=30) is True


def test_old_heartbeat_is_offline() -> None:
    now = datetime(2026, 9, 8, 12, 0, tzinfo=UTC)
    last_seen = now - timedelta(seconds=31)
    assert is_store_online(last_seen, now=now, threshold_seconds=30) is False


def test_naive_timestamp_is_rejected() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        is_store_online(datetime(2026, 9, 8, 12, 0), threshold_seconds=30)


def test_naive_reference_time_is_rejected() -> None:
    aware_last_seen = datetime(2026, 9, 8, 12, 0, tzinfo=UTC)
    with pytest.raises(ValueError, match="now must be timezone-aware"):
        is_store_online(aware_last_seen, now=datetime(2026, 9, 8, 12, 0))


def test_nonpositive_threshold_is_rejected() -> None:
    with pytest.raises(ValueError, match="threshold_seconds must be positive"):
        is_store_online(None, threshold_seconds=0)
