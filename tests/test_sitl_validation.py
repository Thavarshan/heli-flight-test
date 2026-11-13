"""ArduPilot SITL must not accept zero/invalid GPS position as valid."""
import sys
import math
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"code"))
from heli_lib.sitl_validation import valid_navigation


class NavValidation(unittest.TestCase):
    def test_zero_is_uninitialized(self):
        self.assertFalse(valid_navigation(0,0,.14))

    def test_near_home_valid(self):
        self.assertTrue(valid_navigation(34.95416,-117.87323,2.5))

    def test_nonfinite_unresolved(self):
        self.assertFalse(valid_navigation(math.nan,-117.87323,2))

    def test_unrelated_location_not_our_simulator_home(self):
        self.assertFalse(valid_navigation(40,-73,1))


if __name__=="__main__":
    unittest.main()
