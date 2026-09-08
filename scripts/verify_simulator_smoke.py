from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID, uuid4

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SIMULATOR_SERVICES = (
    "simulator-madrid",
    "simulator-london",
    "simulator-new-york",
    "simulator-tokyo",
    "simulator-warsaw",
)
BACKEND_SERVICE = "backend"
DUPLICATE_RE = re.compile(
    r"kind=DUPLICATE status=duplicate[^\r\n]*event_id=([0-9a-fA-F-]{36})"
)


class VerificationError(RuntimeError):
    """Raised when the simulator verification contract is not satisfied."""


@dataclass(frozen=True, slots=True)
class CommandResult:
    stdout: str
    stderr: str
    returncode: int


@dataclass(frozen=True, slots=True)
class TrafficMetrics:
    stores: int
    sales: int
    refunds: int
    late: int

    def satisfies_contract(self) -> bool:
        return self.stores == 5 and self.sales >= 5 and self.refunds >= 1 and self.late >= 1


def _format_command(command: Sequence[str]) -> str:
    return " ".join(command)


def run_command(
    command: Sequence[str],
    *,
    env: dict[str, str] | None = None,
    check: bool = True,
) -> CommandResult:
    completed = subprocess.run(
        list(command),
        cwd=PROJECT_ROOT,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    result = CommandResult(
        stdout=completed.stdout,
        stderr=completed.stderr,
        returncode=completed.returncode,
    )
    if check and completed.returncode != 0:
        details = [
            f"Command failed with exit code {completed.returncode}: {_format_command(command)}"
        ]
        if completed.stdout.strip():
            details.append(f"stdout:\n{completed.stdout.rstrip()}")
        if completed.stderr.strip():
            details.append(f"stderr:\n{completed.stderr.rstrip()}")
        raise VerificationError("\n".join(details))
    return result


def compose(*args: str, env: dict[str, str] | None = None, check: bool = True) -> CommandResult:
    return run_command(("docker", "compose", *args), env=env, check=check)


def read_container_env(name: str) -> str:
    result = compose("exec", "-T", "postgres", "printenv", name)
    value = result.stdout.strip()
    if not value:
        raise VerificationError(f"PostgreSQL container variable {name} is empty.")
    return value


def psql(
    sql: str,
    *,
    db_user: str,
    db_name: str,
    scalar: bool = False,
) -> str:
    args = [
        "exec",
        "-T",
        "postgres",
        "psql",
        "-X",
        "-v",
        "ON_ERROR_STOP=1",
        "-U",
        db_user,
        "-d",
        db_name,
    ]
    if scalar:
        args.extend(("-A", "-t"))
    args.extend(("-c", sql))
    result = compose(*args)
    return result.stdout.strip()


def sql_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def source_pattern(run_tag: str) -> str:
    return f"simulator-%:{run_tag}:%"


def parse_metrics(raw: str) -> TrafficMetrics:
    parts = raw.strip().split("|")
    if len(parts) != 4:
        raise VerificationError(f"Unexpected simulator metrics result: {raw!r}")
    try:
        values = tuple(int(part) for part in parts)
    except ValueError as exc:
        raise VerificationError(f"Simulator metrics are not integers: {raw!r}") from exc
    return TrafficMetrics(*values)


def extract_duplicate_event_id(log_text: str) -> str | None:
    match = DUPLICATE_RE.search(log_text)
    if match is None:
        return None
    event_id = match.group(1)
    try:
        UUID(event_id)
    except ValueError:
        return None
    return event_id


def build_snapshot_sql() -> str:
    return """
SELECT COALESCE(
  json_agg(
    json_build_object(
      'id', id::text,
      'code', code,
      'last_seen_at', last_seen_at,
      'updated_at', updated_at
    )
    ORDER BY code
  ),
  '[]'::json
)::text
FROM stores;
""".strip()


def build_restore_sql(snapshot: list[dict[str, object]]) -> str:
    snapshot_json = json.dumps(snapshot, separators=(",", ":"), ensure_ascii=True)
    encoded = sql_literal(snapshot_json)
    return f"""
WITH snapshot AS (
  SELECT *
  FROM json_to_recordset({encoded}::json)
    AS x(id uuid, code text, last_seen_at timestamptz, updated_at timestamptz)
)
UPDATE stores AS s
SET last_seen_at = snapshot.last_seen_at,
    updated_at = snapshot.updated_at
FROM snapshot
WHERE s.id = snapshot.id;
""".strip()


def build_snapshot_mismatch_sql(snapshot: list[dict[str, object]]) -> str:
    snapshot_json = json.dumps(snapshot, separators=(",", ":"), ensure_ascii=True)
    encoded = sql_literal(snapshot_json)
    return f"""
WITH snapshot AS (
  SELECT *
  FROM json_to_recordset({encoded}::json)
    AS x(id uuid, code text, last_seen_at timestamptz, updated_at timestamptz)
)
SELECT count(*)
FROM snapshot
LEFT JOIN stores AS s ON s.id = snapshot.id
WHERE s.id IS NULL
   OR s.last_seen_at IS DISTINCT FROM snapshot.last_seen_at
   OR s.updated_at IS DISTINCT FROM snapshot.updated_at;
""".strip()


def build_metrics_sql(run_tag: str) -> str:
    pattern = sql_literal(source_pattern(run_tag))
    return f"""
SELECT
  count(DISTINCT store_id),
  count(*) FILTER (WHERE event_type = 'SALE'),
  count(*) FILTER (WHERE event_type = 'REFUND'),
  count(*) FILTER (WHERE occurred_at < received_at - interval '1 second')
FROM pos_events
WHERE source_instance LIKE {pattern};
""".strip()


def build_duplicate_count_sql(run_tag: str, event_id: str) -> str:
    pattern = sql_literal(source_pattern(run_tag))
    event_literal = sql_literal(event_id)
    return f"""
SELECT count(*)
FROM pos_events
WHERE event_id = {event_literal}::uuid
  AND source_instance LIKE {pattern};
""".strip()


def build_delete_sql(run_tag: str, event_type: str) -> str:
    if event_type not in {"SALE", "REFUND"}:
        raise ValueError(f"Unsupported event type for cleanup: {event_type}")
    pattern = sql_literal(source_pattern(run_tag))
    return f"""
DELETE FROM pos_events
WHERE source_instance LIKE {pattern}
  AND event_type = {sql_literal(event_type)};
""".strip()


def build_cleanup_transaction_sql(
    run_tag: str, snapshot: list[dict[str, object]]
) -> str:
    refund_delete = build_delete_sql(run_tag, "REFUND")
    sale_delete = build_delete_sql(run_tag, "SALE")
    restore = build_restore_sql(snapshot)
    return "\n".join(
        (
            "BEGIN;",
            refund_delete,
            sale_delete,
            restore,
            "COMMIT;",
        )
    )


def build_remaining_sql(run_tag: str) -> str:
    pattern = sql_literal(source_pattern(run_tag))
    return f"SELECT count(*) FROM pos_events WHERE source_instance LIKE {pattern};"


def make_smoke_env(run_tag: str) -> dict[str, str]:
    env = os.environ.copy()
    env.update(
        {
            "SIMULATOR_MADRID_EVENTS_PER_SECOND": "2",
            "SIMULATOR_LONDON_EVENTS_PER_SECOND": "2",
            "SIMULATOR_NYC_EVENTS_PER_SECOND": "2",
            "SIMULATOR_TOKYO_EVENTS_PER_SECOND": "2",
            "SIMULATOR_WARSAW_EVENTS_PER_SECOND": "2",
            "SIMULATOR_REFUND_RATE": "1.00",
            "SIMULATOR_DUPLICATE_RATE": "1.00",
            "SIMULATOR_LATE_EVENT_RATE": "1.00",
            "SIMULATOR_STATS_INTERVAL_SECONDS": "5",
            "SIMULATOR_RUN_TAG": run_tag,
        }
    )
    return env


def snapshot_store_state(db_user: str, db_name: str) -> list[dict[str, object]]:
    raw = psql(build_snapshot_sql(), db_user=db_user, db_name=db_name, scalar=True)
    try:
        snapshot = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise VerificationError(f"Could not parse store connectivity snapshot: {raw!r}") from exc
    if not isinstance(snapshot, list) or not snapshot:
        raise VerificationError("Store connectivity snapshot is empty or malformed.")
    for item in snapshot:
        required = {"id", "code", "last_seen_at", "updated_at"}
        if not isinstance(item, dict) or not required <= item.keys():
            raise VerificationError(f"Malformed store snapshot entry: {item!r}")
    return snapshot


def simulator_logs() -> str:
    return compose(
        "--profile",
        "demo",
        "logs",
        "--no-color",
        "--tail=1000",
        *SIMULATOR_SERVICES,
    ).stdout


def show_diagnostics() -> None:
    for command in (
        ("--profile", "demo", "ps"),
        ("--profile", "demo", "logs", "--no-color", "--tail=100", *SIMULATOR_SERVICES),
    ):
        result = compose(*command, check=False)
        if result.stdout.strip():
            print(result.stdout.rstrip(), file=sys.stderr)
        if result.stderr.strip():
            print(result.stderr.rstrip(), file=sys.stderr)


def _running_service_ids(
    services: Sequence[str],
    *,
    profile: str | None = None,
) -> tuple[str, ...]:
    args: list[str] = []
    if profile is not None:
        args.extend(("--profile", profile))
    args.extend(("ps", "--status", "running", "-q", *services))
    result = compose(*args)
    return tuple(line.strip() for line in result.stdout.splitlines() if line.strip())


def _stop_services(
    services: Sequence[str],
    *,
    label: str,
    profile: str | None = None,
) -> None:
    prefix: list[str] = []
    if profile is not None:
        prefix.extend(("--profile", profile))

    stopped = compose(*prefix, "stop", *services, check=False)
    running_after_stop = _running_service_ids(services, profile=profile)
    if stopped.returncode == 0 and not running_after_stop:
        return

    killed = compose(*prefix, "kill", *services, check=False)
    running_after_kill = _running_service_ids(services, profile=profile)
    if killed.returncode == 0 and not running_after_kill:
        return

    details = [f"Could not establish stopped state for {label}."]
    if stopped.stdout.strip():
        details.append(f"stop stdout:\n{stopped.stdout.rstrip()}")
    if stopped.stderr.strip():
        details.append(f"stop stderr:\n{stopped.stderr.rstrip()}")
    if running_after_stop:
        details.append(f"running after stop: {', '.join(running_after_stop)}")
    if killed.stdout.strip():
        details.append(f"kill stdout:\n{killed.stdout.rstrip()}")
    if killed.stderr.strip():
        details.append(f"kill stderr:\n{killed.stderr.rstrip()}")
    if running_after_kill:
        details.append(f"running after kill: {', '.join(running_after_kill)}")
    raise VerificationError("\n".join(details))


def stop_simulators() -> None:
    _stop_services(
        SIMULATOR_SERVICES,
        label="simulator producers",
        profile="demo",
    )


def stop_backend() -> None:
    _stop_services((BACKEND_SERVICE,), label="backend write barrier")


def wait_for_backend_ready(timeout_seconds: float = 30.0) -> None:
    deadline = time.monotonic() + timeout_seconds
    probe = (
        "import urllib.request; "
        "urllib.request.urlopen("
        "'http://localhost:8000/api/v1/health/ready', timeout=2"
        ").read()"
    )
    last_result: CommandResult | None = None
    while time.monotonic() < deadline:
        last_result = compose(
            "exec",
            "-T",
            BACKEND_SERVICE,
            "python",
            "-c",
            probe,
            check=False,
        )
        if last_result.returncode == 0:
            return
        time.sleep(0.5)

    details = [f"Backend did not become ready within {timeout_seconds:.0f} seconds."]
    if last_result is not None and last_result.stderr.strip():
        details.append(f"last probe stderr:\n{last_result.stderr.rstrip()}")
    logs = compose("logs", "--no-color", "--tail=100", BACKEND_SERVICE, check=False)
    if logs.stdout.strip():
        details.append(f"backend logs:\n{logs.stdout.rstrip()}")
    if logs.stderr.strip():
        details.append(f"backend log stderr:\n{logs.stderr.rstrip()}")
    raise VerificationError("\n".join(details))


def start_backend() -> None:
    compose("up", "-d", "--no-deps", BACKEND_SERVICE)
    wait_for_backend_ready()


def verify_no_run_rows(*, run_tag: str, db_user: str, db_name: str) -> None:
    remaining = int(
        psql(build_remaining_sql(run_tag), db_user=db_user, db_name=db_name, scalar=True)
    )
    if remaining != 0:
        raise VerificationError(
            f"Simulator verification cleanup left {remaining} event rows for run tag {run_tag}."
        )


def finalize_verification_run(
    *,
    run_tag: str,
    snapshot: list[dict[str, object]],
    db_user: str,
    db_name: str,
) -> None:
    errors: list[str] = []

    try:
        stop_simulators()
    except Exception as exc:  # noqa: BLE001 - preserve cleanup diagnostics.
        errors.append(f"simulator stop failed: {exc}")
        raise VerificationError("\n".join(errors)) from exc

    backend_stopped = False
    try:
        stop_backend()
        backend_stopped = True
        print("Backend write barrier: PASS")

        cleanup_verification_data(
            run_tag=run_tag,
            snapshot=snapshot,
            db_user=db_user,
            db_name=db_name,
        )
        print("Simulator verification data cleanup: PASS")
    except Exception as exc:  # noqa: BLE001 - cleanup errors are aggregated below.
        errors.append(f"verification data cleanup failed: {exc}")
    finally:
        if backend_stopped:
            try:
                start_backend()
                print("Backend restart readiness: PASS")
            except Exception as exc:  # noqa: BLE001 - preserve restart diagnostics.
                errors.append(f"backend restart failed: {exc}")

    backend_restart_failed = any(
        message.startswith("backend restart failed:") for message in errors
    )
    if backend_stopped and not backend_restart_failed:
        try:
            if _running_service_ids(SIMULATOR_SERVICES, profile="demo"):
                raise VerificationError(
                    "Simulator containers resumed unexpectedly after backend restart."
                )
            time.sleep(0.5)
            verify_no_run_rows(run_tag=run_tag, db_user=db_user, db_name=db_name)
            mismatches = int(
                psql(
                    build_snapshot_mismatch_sql(snapshot),
                    db_user=db_user,
                    db_name=db_name,
                    scalar=True,
                )
            )
            if mismatches != 0:
                raise VerificationError(
                    "Store connectivity restore verification found "
                    f"{mismatches} mismatched rows after backend restart."
                )
            print("Post-restart run isolation: PASS")
            print("Store connectivity restore: PASS")
        except Exception as exc:  # noqa: BLE001 - preserve final-state diagnostics.
            errors.append(f"post-restart verification failed: {exc}")

    if errors:
        raise VerificationError("\n".join(errors))


def cleanup_verification_data(
    *,
    run_tag: str,
    snapshot: list[dict[str, object]],
    db_user: str,
    db_name: str,
) -> None:
    # Cleanup is atomic. REFUND rows are removed before their SALE parents because
    # original_event_id uses a self-referential ON DELETE RESTRICT foreign key. If any
    # statement fails, PostgreSQL rolls back the entire cleanup transaction and psql's
    # captured stderr identifies the real database error.
    transaction = build_cleanup_transaction_sql(run_tag, snapshot)
    psql(transaction, db_user=db_user, db_name=db_name)

    verify_no_run_rows(run_tag=run_tag, db_user=db_user, db_name=db_name)

    mismatches = int(
        psql(
            build_snapshot_mismatch_sql(snapshot),
            db_user=db_user,
            db_name=db_name,
            scalar=True,
        )
    )
    if mismatches != 0:
        raise VerificationError(
            f"Store connectivity restore verification found {mismatches} mismatched rows."
        )


def run_smoke(timeout_seconds: int) -> None:
    run_tag = "verify-" + uuid4().hex[:12]
    smoke_env = make_smoke_env(run_tag)
    db_user = read_container_env("POSTGRES_USER")
    db_name = read_container_env("POSTGRES_DB")
    snapshot = snapshot_store_state(db_user, db_name)

    smoke_error: Exception | None = None
    cleanup_errors: list[str] = []
    evidence_printed = False

    try:
        compose(
            "--profile",
            "demo",
            "up",
            "-d",
            "--build",
            "--force-recreate",
            "--no-deps",
            *SIMULATOR_SERVICES,
            env=smoke_env,
        )

        deadline = time.monotonic() + timeout_seconds
        metrics = TrafficMetrics(0, 0, 0, 0)
        duplicate_event_id: str | None = None

        while time.monotonic() < deadline:
            time.sleep(1)
            metrics = parse_metrics(
                psql(build_metrics_sql(run_tag), db_user=db_user, db_name=db_name, scalar=True)
            )
            duplicate_event_id = extract_duplicate_event_id(simulator_logs())
            if metrics.satisfies_contract() and duplicate_event_id is not None:
                duplicate_rows = int(
                    psql(
                        build_duplicate_count_sql(run_tag, duplicate_event_id),
                        db_user=db_user,
                        db_name=db_name,
                        scalar=True,
                    )
                )
                if duplicate_rows == 1:
                    print("Simulator traffic observed from exactly 5 stores.")
                    print(f"Persisted SALE rows: {metrics.sales}")
                    print(f"Persisted REFUND rows: {metrics.refunds}")
                    print(f"Persisted late rows: {metrics.late}")
                    print("Exact duplicate replay observed: yes")
                    print(f"Duplicate replay durable row count: {duplicate_rows}")
                    print(f"Verification run tag: {run_tag}")
                    evidence_printed = True
                    break

        if not evidence_printed:
            raise VerificationError(
                "Simulator smoke timed out: "
                f"stores={metrics.stores} sales={metrics.sales} refunds={metrics.refunds} "
                f"late={metrics.late} duplicate={duplicate_event_id is not None}."
            )
    except Exception as exc:  # noqa: BLE001 - preserve the original verification failure.
        smoke_error = exc
        show_diagnostics()
    finally:
        try:
            finalize_verification_run(
                run_tag=run_tag,
                snapshot=snapshot,
                db_user=db_user,
                db_name=db_name,
            )
        except Exception as exc:  # noqa: BLE001 - cleanup errors are reported separately.
            cleanup_errors.append(str(exc))

    if smoke_error is not None:
        if cleanup_errors:
            print("Cleanup diagnostics:", file=sys.stderr)
            for message in cleanup_errors:
                print(f"- {message}", file=sys.stderr)
        raise VerificationError(str(smoke_error)) from smoke_error

    if cleanup_errors:
        raise VerificationError("\n".join(cleanup_errors))


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify five StorePulse POS simulator producers.")
    parser.add_argument(
        "--timeout",
        type=int,
        default=35,
        help="Maximum seconds to wait for the simulator evidence contract (default: 35).",
    )
    args = parser.parse_args(argv)
    if args.timeout < 5:
        parser.error("--timeout must be at least 5 seconds")
    return args


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        run_smoke(args.timeout)
    except VerificationError as exc:
        print(f"Simulator verification failed:\n{exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
