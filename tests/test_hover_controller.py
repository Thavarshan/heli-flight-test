"""Pure-function tests for the exploratory controller, not flight validation."""
import math
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "code"))
from heli_lib.hover_controller import compute_hold_commands, HoldGains

STATE = {"north_m": 0., "east_m": 0., "agl_m": 15.,
         "psi_rad": 0., "u_mps": 0., "v_mps": 0., "climb_mps": 0.}
TARGET = {"north_m": 0., "east_m": 0., "agl_m": 15.}
NOMINAL = {"collective": 0.615, "longitudinal": -0.18,
           "lateral": 0.22, "pedal": 0.39}

class HoverControllerTests(unittest.TestCase):
    def test_zero_error_retains_baseline(self):
        self.assertEqual(compute_hold_commands(STATE, TARGET, NOMINAL), NOMINAL)

    def test_forward_speed_hypothesis_requires_cyclic_correction(self):
        x = {**STATE, "u_mps": 1.0}
        self.assertLess(compute_hold_commands(x, TARGET, NOMINAL)["longitudinal"],
                        NOMINAL["longitudinal"])

    def test_world_to_body_rotation(self):
        x = {**STATE, "psi_rad": math.pi / 2, "north_m": 2.0}
        result = compute_hold_commands(x, TARGET, NOMINAL)
        self.assertGreater(result["lateral"], NOMINAL["lateral"])

    def test_altitude_and_climb_feedback(self):
        low = {**STATE, "agl_m": 14.0}
        rising = {**STATE, "climb_mps": 1.0}
        self.assertGreater(compute_hold_commands(low, TARGET, NOMINAL)["collective"],
                           NOMINAL["collective"])
        self.assertLess(compute_hold_commands(rising, TARGET, NOMINAL)["collective"],
                        NOMINAL["collective"])

    def test_saturates_at_declared_limits(self):
        x = {**STATE, "north_m": 1e6, "east_m": 1e6, "agl_m": -1e6}
        out = compute_hold_commands(x, TARGET, NOMINAL)
        self.assertAlmostEqual(out["longitudinal"], NOMINAL["longitudinal"] - 0.14)
        self.assertAlmostEqual(out["lateral"], NOMINAL["lateral"] - 0.14)
        self.assertAlmostEqual(out["collective"], NOMINAL["collective"] + 0.14)

    def test_refuses_nonfinite_or_missing_inputs(self):
        for x in ({**STATE, "u_mps": float("nan")},
                  {k: v for k, v in STATE.items() if k != "u_mps"}):
            with self.subTest(x=x), self.assertRaises(ValueError):
                compute_hold_commands(x, TARGET, NOMINAL)

    def test_refuses_invalid_gains(self):
        with self.assertRaises(ValueError):
            compute_hold_commands(STATE, TARGET, NOMINAL, HoldGains(cyclic_limit=-1))

if __name__ == "__main__":
    unittest.main()
