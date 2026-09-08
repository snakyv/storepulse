from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass


def _parse_float(env: Mapping[str, str], name: str, default: float) -> float:
    raw = env.get(name)
    if raw is None or raw == "":
        return default
    try:
        return float(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be a number") from exc


def _parse_int(env: Mapping[str, str], name: str, default: int) -> int:
    raw = env.get(name)
    if raw is None or raw == "":
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer") from exc


@dataclass(frozen=True, slots=True)
class SimulatorConfig:
    backend_url: str
    store_code: str
    instance_label: str
    run_tag: str
    heartbeat_interval: float
    events_per_second: float
    refund_rate: float
    duplicate_rate: float
    late_event_rate: float
    max_late_seconds: int
    max_quantity: int
    request_timeout_seconds: float
    retry_initial_seconds: float
    retry_max_seconds: float
    retry_jitter_ratio: float
    max_retry_attempts: int
    queue_size: int
    worker_count: int
    stats_interval_seconds: float
    random_seed: int

    @classmethod
    def from_env(cls, env: Mapping[str, str]) -> SimulatorConfig:
        backend_url = env.get("BACKEND_URL", "http://localhost:8000").rstrip("/")
        store_code = env.get("STORE_CODE", "MAD-MADRID").strip()
        instance_label = env.get("INSTANCE_LABEL", "storepulse-pos").strip()
        run_tag = env.get("RUN_TAG", "demo").strip()
        config = cls(
            backend_url=backend_url,
            store_code=store_code,
            instance_label=instance_label,
            run_tag=run_tag,
            heartbeat_interval=_parse_float(env, "HEARTBEAT_INTERVAL", 5.0),
            events_per_second=_parse_float(env, "EVENTS_PER_SECOND", 1.0),
            refund_rate=_parse_float(env, "REFUND_RATE", 0.20),
            duplicate_rate=_parse_float(env, "DUPLICATE_RATE", 0.08),
            late_event_rate=_parse_float(env, "LATE_EVENT_RATE", 0.10),
            max_late_seconds=_parse_int(env, "MAX_LATE_SECONDS", 7200),
            max_quantity=_parse_int(env, "MAX_QUANTITY", 3),
            request_timeout_seconds=_parse_float(env, "REQUEST_TIMEOUT_SECONDS", 5.0),
            retry_initial_seconds=_parse_float(env, "RETRY_INITIAL_SECONDS", 0.25),
            retry_max_seconds=_parse_float(env, "RETRY_MAX_SECONDS", 5.0),
            retry_jitter_ratio=_parse_float(env, "RETRY_JITTER_RATIO", 0.20),
            max_retry_attempts=_parse_int(env, "MAX_RETRY_ATTEMPTS", 0),
            queue_size=_parse_int(env, "QUEUE_SIZE", 1000),
            worker_count=_parse_int(env, "WORKER_COUNT", 2),
            stats_interval_seconds=_parse_float(env, "STATS_INTERVAL_SECONDS", 30.0),
            random_seed=_parse_int(env, "RANDOM_SEED", 1),
        )
        config.validate()
        return config

    def validate(self) -> None:
        if not self.backend_url:
            raise ValueError("BACKEND_URL must not be empty")
        if not self.store_code:
            raise ValueError("STORE_CODE must not be empty")
        if not self.instance_label:
            raise ValueError("INSTANCE_LABEL must not be empty")
        if not self.run_tag:
            raise ValueError("RUN_TAG must not be empty")
        if self.heartbeat_interval <= 0:
            raise ValueError("HEARTBEAT_INTERVAL must be positive")
        if self.events_per_second <= 0:
            raise ValueError("EVENTS_PER_SECOND must be positive")
        for name, value in (
            ("REFUND_RATE", self.refund_rate),
            ("DUPLICATE_RATE", self.duplicate_rate),
            ("LATE_EVENT_RATE", self.late_event_rate),
        ):
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be between 0 and 1")
        if self.max_late_seconds < 1:
            raise ValueError("MAX_LATE_SECONDS must be at least 1")
        if self.max_quantity < 1:
            raise ValueError("MAX_QUANTITY must be at least 1")
        if self.request_timeout_seconds <= 0:
            raise ValueError("REQUEST_TIMEOUT_SECONDS must be positive")
        if self.retry_initial_seconds < 0:
            raise ValueError("RETRY_INITIAL_SECONDS must be non-negative")
        if self.retry_max_seconds < self.retry_initial_seconds:
            raise ValueError("RETRY_MAX_SECONDS must be >= RETRY_INITIAL_SECONDS")
        if not 0.0 <= self.retry_jitter_ratio <= 1.0:
            raise ValueError("RETRY_JITTER_RATIO must be between 0 and 1")
        if self.max_retry_attempts < 0:
            raise ValueError("MAX_RETRY_ATTEMPTS must be non-negative")
        if self.queue_size < 1:
            raise ValueError("QUEUE_SIZE must be at least 1")
        if self.worker_count < 1:
            raise ValueError("WORKER_COUNT must be at least 1")
        if self.stats_interval_seconds <= 0:
            raise ValueError("STATS_INTERVAL_SECONDS must be positive")
