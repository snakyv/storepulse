from __future__ import annotations

import unittest

from simulator.config import SimulatorConfig


class SimulatorConfigTests(unittest.TestCase):
    def test_parses_runtime_configuration(self) -> None:
        config = SimulatorConfig.from_env(
            {
                "BACKEND_URL": "http://backend:8000/",
                "STORE_CODE": "MAD-TOKYO",
                "INSTANCE_LABEL": "simulator-tokyo",
                "RUN_TAG": "unit",
                "EVENTS_PER_SECOND": "2.5",
                "REFUND_RATE": "0.25",
                "DUPLICATE_RATE": "0.1",
                "LATE_EVENT_RATE": "0.2",
                "RANDOM_SEED": "404",
            }
        )

        self.assertEqual(config.backend_url, "http://backend:8000")
        self.assertEqual(config.store_code, "MAD-TOKYO")
        self.assertEqual(config.instance_label, "simulator-tokyo")
        self.assertEqual(config.run_tag, "unit")
        self.assertEqual(config.events_per_second, 2.5)
        self.assertEqual(config.refund_rate, 0.25)
        self.assertEqual(config.duplicate_rate, 0.1)
        self.assertEqual(config.late_event_rate, 0.2)
        self.assertEqual(config.random_seed, 404)

    def test_rejects_invalid_rate(self) -> None:
        with self.assertRaisesRegex(ValueError, "REFUND_RATE"):
            SimulatorConfig.from_env({"REFUND_RATE": "1.1"})

    def test_rejects_non_positive_intensity(self) -> None:
        with self.assertRaisesRegex(ValueError, "EVENTS_PER_SECOND"):
            SimulatorConfig.from_env({"EVENTS_PER_SECOND": "0"})


if __name__ == "__main__":
    unittest.main()
