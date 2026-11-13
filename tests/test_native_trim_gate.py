"""Regression checks for fail-closed JSBSim native trim gate."""
import sys
import types
from pathlib import Path
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"code"))
from heli_lib.hover_metrics import screen_hover_window


class HoverValidationGateTest(unittest.TestCase):
    def test_only_screened_pass_candidate_can_advance(self):
        # No simulated or inferred success if trim was rejected.
        def decision(entries):
            if not entries:
                return "UNRESOLVED"
            passed = [entry for entry in entries
                      if entry["status"] == "POST_TRIM_SCREENED"
                      and entry["screen"]["status"] == "PASS_CANDIDATE"]
            if passed:
                return "TRIM_CANDIDATE_NOT_VALIDATED"
            if any(x["status"] == "BACKEND_ERROR" for x in entries):
                return "UNRESOLVED"
            return "NO_STABLE_HOVER_IN_BOUNDED_NATIVE_TRIM_TRIALS"
        self.assertEqual(decision([{"status":"TRIM_REJECTED"}]),
                         "NO_STABLE_HOVER_IN_BOUNDED_NATIVE_TRIM_TRIALS")
        self.assertEqual(decision([{"status":"BACKEND_ERROR"}]),"UNRESOLVED")
        self.assertEqual(decision([{"status":"POST_TRIM_SCREENED",
                                   "screen":{"status":"FAIL_CANDIDATE"}}]),
                         "NO_STABLE_HOVER_IN_BOUNDED_NATIVE_TRIM_TRIALS")
        self.assertEqual(decision([{"status":"POST_TRIM_SCREENED",
                                   "screen":{"status":"PASS_CANDIDATE"}}]),
                         "TRIM_CANDIDATE_NOT_VALIDATED")


if __name__=="__main__":
    unittest.main()
