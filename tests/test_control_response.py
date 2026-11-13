"""Offline tests: paired perturbations are not aircraft-sign certification."""
import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "code"))
from heli_lib.control_response import classify_pair, PRIMARY_READOUTS


class ControlResponseTests(unittest.TestCase):
    def test_positive_response(self):
        result = classify_pair(0.0, -2.0, 2.0, 0.1)
        self.assertEqual(result["status"], "POSITIVE_MONOTONE")
        self.assertEqual(result["central_difference_per_normalized_command"], 20.0)

    def test_negative_response(self):
        self.assertEqual(classify_pair(0, 1, -1, 0.05)["status"], "NEGATIVE_MONOTONE")

    def test_nonmonotone_is_not_reversed_sign(self):
        self.assertEqual(classify_pair(1, 2, 3, 0.1)["status"], "NONMONOTONE_OR_DRIFT")

    def test_no_response(self):
        self.assertEqual(classify_pair(4, 4, 4, 0.1)["status"], "NO_MEASURABLE_RESPONSE")

    def test_nonfinite_is_unresolved(self):
        self.assertEqual(classify_pair(0, math.nan, 1, 0.1)["status"], "UNRESOLVED")

    def test_bad_step_rejected(self):
        for invalid in (0, -1):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                classify_pair(0, -1, 1, invalid)

    def test_each_primary_readout_is_declared(self):
        self.assertEqual(set(PRIMARY_READOUTS),
                         {"collective", "longitudinal", "lateral", "pedal"})


if __name__ == "__main__":
    unittest.main()
