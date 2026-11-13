"""Pure unit tests; no JSBSim requirement."""
import math
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "code"))
from heli_lib.numerical_validation import UNITS, compare_traces


def sample(n, *, offset=0.0):
    return [{"time_s": i * .15,
             **{key: (float(i) + offset if key == "north_m" else 1.0)
                for key in UNITS}}
            for i in range(n)]


class NumericalValidationTests(unittest.TestCase):
    def test_zero_difference(self):
        x = sample(3)
        r = compare_traces(x, x, expected_period_s=.15)
        self.assertEqual(r["status"], "DESCRIPTIVE_ONLY")
        self.assertEqual(r["max_abs_difference"]["north_m"], 0.0)

    def test_difference_reports_si_values(self):
        r = compare_traces(sample(3), sample(3, offset=2.0),
                           expected_period_s=.15)
        self.assertEqual(r["max_abs_difference"]["north_m"], 2.0)
        self.assertEqual(r["rms_difference"]["north_m"], 2.0)
        self.assertEqual(r["units"]["north_m"], "m")

    def test_mismatched_lengths_are_unresolved(self):
        self.assertEqual(compare_traces(sample(3), sample(2),
                         expected_period_s=.15)["reason"],
                         "incompatible_trace_lengths")

    def test_missing_data_is_unresolved(self):
        x = sample(2)
        del x[0]["rotor_rpm"]
        self.assertEqual(compare_traces(x, sample(2),
                         expected_period_s=.15)["status"], "UNRESOLVED")

    def test_nonfinite_is_unresolved(self):
        x = sample(3)
        x[2]["north_m"] = math.inf
        self.assertEqual(compare_traces(sample(3), x,
                         expected_period_s=.15)["reason"], "nonfinite_input")

    def test_duplicate_or_irregular_timestamps_are_unresolved(self):
        x = sample(3)
        x[2]["time_s"] = x[1]["time_s"]
        self.assertEqual(compare_traces(sample(3), x,
                         expected_period_s=.15)["reason"],
                         "invalid_observation_clock")

    def test_shifted_physical_timestamps_are_unresolved(self):
        x = sample(3)
        for row in x:
            row["time_s"] += .05
        self.assertEqual(compare_traces(sample(3), x,
                         expected_period_s=.15)["reason"],
                         "unaligned_physical_timestamps")

    def test_period_must_be_positive(self):
        with self.assertRaises(ValueError):
            compare_traces(sample(2), sample(2), expected_period_s=0.0)


if __name__ == "__main__":
    unittest.main()
