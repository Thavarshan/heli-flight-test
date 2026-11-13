"""Tests the real trim gate, independent of the JSBSim installation."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "code"))
from heli_lib.trim_gate import decide


class HoverValidationGateTest(unittest.TestCase):
    def test_empty_is_unresolved(self):
        self.assertEqual(decide([]), "UNRESOLVED")

    def test_trim_rejection_does_not_advance(self):
        self.assertEqual(
            decide([{"status":"TRIM_REJECTED"}]),
            "NO_STABLE_HOVER_IN_BOUNDED_NATIVE_TRIM_TRIALS",
        )

    def test_backend_error_is_not_a_control_failure(self):
        self.assertEqual(decide([{"status":"BACKEND_ERROR"}]), "UNRESOLVED")

    def test_screen_failure_blocks(self):
        self.assertEqual(
            decide([{"status":"POST_TRIM_SCREENED",
                     "screen":{"status":"FAIL_CANDIDATE"}}]),
            "NO_STABLE_HOVER_IN_BOUNDED_NATIVE_TRIM_TRIALS",
        )

    def test_still_not_model_validated_if_screen_passes(self):
        self.assertEqual(
            decide([{"status":"POST_TRIM_SCREENED",
                     "screen":{"status":"PASS_CANDIDATE"}}]),
            "TRIM_CANDIDATE_NOT_VALIDATED",
        )


if __name__ == "__main__":
    unittest.main()
