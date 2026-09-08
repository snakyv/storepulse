from __future__ import annotations

import unittest
from unittest.mock import Mock, patch
from uuid import uuid4

from scripts.verify_simulator_smoke import (
    CommandResult,
    TrafficMetrics,
    VerificationError,
    build_cleanup_transaction_sql,
    build_delete_sql,
    build_restore_sql,
    cleanup_verification_data,
    extract_duplicate_event_id,
    finalize_verification_run,
    parse_metrics,
    run_command,
    source_pattern,
    stop_simulators,
)


class SimulatorSmokeHelperTests(unittest.TestCase):
    def test_parse_metrics_and_contract(self) -> None:
        metrics = parse_metrics("5|12|4|9\n")
        self.assertEqual(metrics, TrafficMetrics(stores=5, sales=12, refunds=4, late=9))
        self.assertTrue(metrics.satisfies_contract())

    def test_contract_rejects_missing_store(self) -> None:
        self.assertFalse(TrafficMetrics(stores=4, sales=12, refunds=4, late=9).satisfies_contract())

    def test_duplicate_event_id_extraction(self) -> None:
        event_id = str(uuid4())
        logs = f"kind=DUPLICATE status=duplicate store=MAD-MADRID event_id={event_id}"
        self.assertEqual(extract_duplicate_event_id(logs), event_id)

    def test_duplicate_extraction_ignores_unrelated_logs(self) -> None:
        self.assertIsNone(extract_duplicate_event_id("kind=SALE status=accepted"))

    def test_cleanup_deletes_refunds_and_sales_with_isolated_pattern(self) -> None:
        run_tag = "verify-abc123"
        self.assertEqual(source_pattern(run_tag), "simulator-%:verify-abc123:%")
        refund_sql = build_delete_sql(run_tag, "REFUND")
        sale_sql = build_delete_sql(run_tag, "SALE")
        self.assertIn("event_type = 'REFUND'", refund_sql)
        self.assertIn("event_type = 'SALE'", sale_sql)
        self.assertIn("verify-abc123", refund_sql)
        self.assertIn("verify-abc123", sale_sql)

    def test_cleanup_transaction_is_atomic_and_fk_safe(self) -> None:
        snapshot = [
            {
                "id": str(uuid4()),
                "code": "MAD-MADRID",
                "last_seen_at": None,
                "updated_at": "2026-09-09T00:00:00+00:00",
            }
        ]
        sql = build_cleanup_transaction_sql("verify-abc123", snapshot)
        self.assertTrue(sql.startswith("BEGIN;"))
        self.assertTrue(sql.rstrip().endswith("COMMIT;"))
        refund_index = sql.index("event_type = 'REFUND'")
        sale_index = sql.index("event_type = 'SALE'")
        restore_index = sql.index("UPDATE stores")
        self.assertLess(refund_index, sale_index)
        self.assertLess(sale_index, restore_index)

    def test_cleanup_executes_transaction_then_verifies_state(self) -> None:
        snapshot = [
            {
                "id": str(uuid4()),
                "code": "MAD-MADRID",
                "last_seen_at": None,
                "updated_at": "2026-09-09T00:00:00+00:00",
            }
        ]
        with patch("scripts.verify_simulator_smoke.psql") as mocked_psql:
            mocked_psql.side_effect = ["BEGIN\nDELETE 2\nDELETE 1\nUPDATE 1\nCOMMIT", "0", "0"]
            cleanup_verification_data(
                run_tag="verify-abc123",
                snapshot=snapshot,
                db_user="storepulse",
                db_name="storepulse",
            )

        sql_calls = [call.args[0] for call in mocked_psql.call_args_list]
        self.assertIn("BEGIN;", sql_calls[0])
        self.assertIn("event_type = 'REFUND'", sql_calls[0])
        self.assertIn("event_type = 'SALE'", sql_calls[0])
        self.assertIn("UPDATE stores", sql_calls[0])
        self.assertIn("SELECT count(*)", sql_calls[1])
        self.assertIn("IS DISTINCT FROM", sql_calls[2])

    def test_restore_sql_handles_null_and_timestamp_values(self) -> None:
        snapshot = [
            {
                "id": str(uuid4()),
                "code": "MAD-MADRID",
                "last_seen_at": None,
                "updated_at": "2026-09-09T00:00:00+00:00",
            },
            {
                "id": str(uuid4()),
                "code": "MAD-TOKYO",
                "last_seen_at": "2026-09-09T00:00:00+00:00",
                "updated_at": "2026-09-09T00:01:00+00:00",
            },
        ]
        sql = build_restore_sql(snapshot)
        self.assertIn("json_to_recordset", sql)
        self.assertIn("last_seen_at timestamptz", sql)
        self.assertIn("updated_at timestamptz", sql)
        self.assertIn("MAD-MADRID", sql)
        self.assertIn("2026-09-09T00:00:00+00:00", sql)

    def test_cleanup_rejects_unknown_event_type(self) -> None:
        with self.assertRaises(ValueError):
            build_delete_sql("verify-abc123", "UNKNOWN")

    def test_stop_uses_kill_fallback_when_graceful_stop_fails(self) -> None:
        failed = CommandResult(stdout="", stderr="stop failed", returncode=1)
        still_running = CommandResult(stdout="container-1\n", stderr="", returncode=0)
        killed = CommandResult(stdout="", stderr="", returncode=0)
        stopped = CommandResult(stdout="", stderr="", returncode=0)
        with patch(
            "scripts.verify_simulator_smoke.compose",
            side_effect=[failed, still_running, killed, stopped],
        ) as mocked:
            stop_simulators()
        self.assertEqual(mocked.call_count, 4)

    def test_stop_accepts_verified_graceful_stop(self) -> None:
        stopped = CommandResult(stdout="", stderr="", returncode=0)
        not_running = CommandResult(stdout="", stderr="", returncode=0)
        with patch(
            "scripts.verify_simulator_smoke.compose",
            side_effect=[stopped, not_running],
        ) as mocked:
            stop_simulators()
        self.assertEqual(mocked.call_count, 2)

    def test_stop_reports_failure_when_service_remains_running(self) -> None:
        failed_stop = CommandResult(stdout="", stderr="stop failed", returncode=1)
        running_after_stop = CommandResult(stdout="container-1\n", stderr="", returncode=0)
        failed_kill = CommandResult(stdout="", stderr="kill failed", returncode=1)
        running_after_kill = CommandResult(stdout="container-1\n", stderr="", returncode=0)
        with patch(
            "scripts.verify_simulator_smoke.compose",
            side_effect=[
                failed_stop,
                running_after_stop,
                failed_kill,
                running_after_kill,
            ],
        ):
            with self.assertRaises(VerificationError) as captured:
                stop_simulators()
        message = str(captured.exception)
        self.assertIn("stop failed", message)
        self.assertIn("kill failed", message)
        self.assertIn("running after kill", message)

    def test_finalize_uses_backend_write_barrier_before_cleanup(self) -> None:
        snapshot = [
            {
                "id": str(uuid4()),
                "code": "MAD-MADRID",
                "last_seen_at": None,
                "updated_at": "2026-09-09T00:00:00+00:00",
            }
        ]
        order: list[str] = []

        def mark(name: str):
            def callback(*args, **kwargs):
                order.append(name)
                return () if name == "running-services" else None

            return callback

        with (
            patch("scripts.verify_simulator_smoke.stop_simulators", side_effect=mark("simulators")),
            patch("scripts.verify_simulator_smoke.stop_backend", side_effect=mark("backend-stop")),
            patch(
                "scripts.verify_simulator_smoke.cleanup_verification_data",
                side_effect=mark("cleanup"),
            ),
            patch(
                "scripts.verify_simulator_smoke.start_backend",
                side_effect=mark("backend-start"),
            ),
            patch(
                "scripts.verify_simulator_smoke._running_service_ids",
                side_effect=mark("running-services"),
            ),
            patch(
                "scripts.verify_simulator_smoke.verify_no_run_rows",
                side_effect=mark("no-run-rows"),
            ),
            patch("scripts.verify_simulator_smoke.psql", return_value="0"),
            patch("scripts.verify_simulator_smoke.time.sleep"),
        ):
            finalize_verification_run(
                run_tag="verify-abc123",
                snapshot=snapshot,
                db_user="storepulse",
                db_name="storepulse",
            )

        self.assertEqual(
            order[:4],
            ["simulators", "backend-stop", "cleanup", "backend-start"],
        )
        self.assertIn("running-services", order)
        self.assertIn("no-run-rows", order)

    def test_finalize_restarts_backend_when_cleanup_fails(self) -> None:
        snapshot = [
            {
                "id": str(uuid4()),
                "code": "MAD-MADRID",
                "last_seen_at": None,
                "updated_at": "2026-09-09T00:00:00+00:00",
            }
        ]
        with (
            patch("scripts.verify_simulator_smoke.stop_simulators"),
            patch("scripts.verify_simulator_smoke.stop_backend"),
            patch(
                "scripts.verify_simulator_smoke.cleanup_verification_data",
                side_effect=VerificationError("cleanup exploded"),
            ),
            patch("scripts.verify_simulator_smoke.start_backend") as mocked_start,
            patch("scripts.verify_simulator_smoke._running_service_ids", return_value=()),
            patch("scripts.verify_simulator_smoke.verify_no_run_rows"),
            patch("scripts.verify_simulator_smoke.psql", return_value="0"),
            patch("scripts.verify_simulator_smoke.time.sleep"),
        ):
            with self.assertRaises(VerificationError) as captured:
                finalize_verification_run(
                    run_tag="verify-abc123",
                    snapshot=snapshot,
                    db_user="storepulse",
                    db_name="storepulse",
                )

        mocked_start.assert_called_once_with()
        self.assertIn("cleanup exploded", str(captured.exception))

    def test_finalize_skips_db_cleanup_when_simulator_stop_fails(self) -> None:
        with (
            patch(
                "scripts.verify_simulator_smoke.stop_simulators",
                side_effect=VerificationError("still running"),
            ),
            patch("scripts.verify_simulator_smoke.stop_backend") as mocked_backend_stop,
            patch(
                "scripts.verify_simulator_smoke.cleanup_verification_data"
            ) as mocked_cleanup,
        ):
            with self.assertRaises(VerificationError) as captured:
                finalize_verification_run(
                    run_tag="verify-abc123",
                    snapshot=[],
                    db_user="storepulse",
                    db_name="storepulse",
                )

        mocked_backend_stop.assert_not_called()
        mocked_cleanup.assert_not_called()
        self.assertIn("still running", str(captured.exception))

    def test_command_failure_preserves_stderr_for_diagnostics(self) -> None:
        completed = Mock(returncode=1, stdout="partial stdout\n", stderr="database detail\n")
        with patch("scripts.verify_simulator_smoke.subprocess.run", return_value=completed):
            with self.assertRaises(VerificationError) as captured:
                run_command(("docker", "compose", "exec"))

        message = str(captured.exception)
        self.assertIn("exit code 1", message)
        self.assertIn("partial stdout", message)
        self.assertIn("database detail", message)


if __name__ == "__main__":
    unittest.main()
