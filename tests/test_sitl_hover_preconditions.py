"""Pure post-takeoff hover diagnostic; SITL is not needed."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"code"))
from heli_lib.sitl_validation import valid_navigation


class HoverPreconditionsTest(unittest.TestCase):
    def test_bad_coordinates_are_not_nav(self):
        self.assertFalse(valid_navigation(0,0,0.1))
    def test_source_home_valid(self):
        self.assertTrue(valid_navigation(34.95416,-117.87323,8.0))


if __name__=="__main__":
    unittest.main()
