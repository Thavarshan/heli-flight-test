"""Pure-Python tests for the exploratory hover stationarity screen."""
import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "code"))
from heli_lib.hover_metrics import REQUIRED, screen_hover_window


def trajectory(*, drift=0.0, speed=0.0, altitude_ft=100.0, rotor_rpm=300.0):
    rows = []
    for step in range(61):
        t = step * 0.5
        state = {
            "simulation/sim-time-sec": t,
            "position/h-agl-ft": altitude_ft,
            "position/distance-from-start-lat-mt": drift * t,
            "position/distance-from-start-lon-mt": 0.0,
            "attitude/phi-rad": 0.0,
            "attitude/theta-rad": 0.0,
            "velocities/u-fps": speed,
            "velocities/v-fps": 0.0,
            "velocities/w-fps": 0.0,
            "propulsion/engine/rotor-rpm": rotor_rpm,
        }
        rows.append([state[name] for name in REQUIRED])
    return rows


class HoverScreenTests(unittest.TestCase):
    def test_stationary_airborne_trace_is_a_candidate_not_validation(self):
        result = screen_hover_window(REQUIRED, trajectory())
        self.assertEqual(result["status"], "PASS_CANDIDATE")
        self.assertEqual(result["samples"], 41)

    def test_rejects_horizontal_drift_even_when_body_velocity_is_zero(self):
        result = screen_hover_window(REQUIRED, trajectory(drift=0.5))
        self.assertEqual(result["status"], "FAIL_CANDIDATE")
        self.assertFalse(result["criteria"]["max_horizontal_excursion_m"])

    def test_rejects_fast_motion(self):
        result = screen_hover_window(REQUIRED, trajectory(speed=6.0))
        self.assertEqual(result["status"], "FAIL_CANDIDATE")
        self.assertFalse(result["criteria"]["max_body_speed_mps"])

    def test_grounded_or_stopped_rotor_is_not_hover(self):
        for kw in ({"altitude_ft": 0.0}, {"rotor_rpm": 0.0}):
            with self.subTest(kw=kw):
                self.assertEqual(
                    screen_hover_window(REQUIRED, trajectory(**kw))["status"],
                    "FAIL_CANDIDATE",
                )

    def test_missing_required_telemetry_is_unresolved(self):
        names = list(REQUIRED[:-1])
        self.assertEqual(
            screen_hover_window(names, [row[:-1] for row in trajectory()])["status"],
            "UNRESOLVED",
        )

    def test_nonfinite_and_duplicate_time_are_unresolved(self):
        bad = trajectory()
        bad[-1][REQUIRED.index("attitude/phi-rad")] = math.nan
        self.assertEqual(screen_hover_window(REQUIRED, bad)["reason"], "nonfinite_value")
        bad = trajectory()
        bad[-1][0] = bad[-2][0]
        self.assertEqual(
            screen_hover_window(REQUIRED, bad)["reason"], "non_increasing_timestamps"
        )

    def test_bad_sampling_and_short_coverage_are_unresolved(self):
        short = trajectory()[:10]
        self.assertEqual(screen_hover_window(REQUIRED, short)["reason"], "insufficient_duration")
        sparse = trajectory()[::6]
        self.assertEqual(screen_hover_window(REQUIRED, sparse)["reason"], "sample_gap_exceeds_limit")

    def test_invalid_configuration_rejected(self):
        with self.assertRaises(ValueError):
            screen_hover_window(REQUIRED, trajectory(), window_s=math.nan)


if __name__ == "__main__":
    unittest.main()
