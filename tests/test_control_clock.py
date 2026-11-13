import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "code"))
from heli_lib.control_clock import SimulationClock


class ControlClockTests(unittest.TestCase):
    def test_identical_physical_update_times(self):
        observed = []
        for dt in (0.0075, 0.00375, 0.001875):
            clock = SimulationClock(dt)
            self.assertEqual(clock.control_ticks, round(.15 / dt))
            timestamps = [round(clock.time_s(i), 9)
                          for i in range(clock.ticks_for_duration(4.5) + 1)
                          if clock.is_control_tick(i)]
            observed.append(timestamps)
        self.assertEqual(observed[0], observed[1])
        self.assertEqual(observed[0], observed[2])
        self.assertEqual(observed[0][0], 0.)
        self.assertEqual(observed[0][-1], 4.5)

    def test_independent_control_and_observation_period(self):
        clock = SimulationClock(.0075, .075, .15)
        self.assertEqual(clock.control_ticks, 10)
        self.assertEqual(clock.observation_ticks, 20)
        self.assertTrue(clock.is_control_tick(10))
        self.assertFalse(clock.is_observation_tick(10))

    def test_unrepresentable_period_is_rejected(self):
        for dt in (.013, .037):
            with self.subTest(dt=dt), self.assertRaises(ValueError):
                SimulationClock(dt)

    def test_reject_invalid_inputs(self):
        for x in (0, -1, math.nan, math.inf):
            with self.subTest(x=x), self.assertRaises(ValueError):
                SimulationClock(x)
        with self.assertRaises(ValueError):
            SimulationClock(.0075).ticks_for_duration(.01)

    def test_initial_update_happens_at_zero(self):
        clock = SimulationClock(.0075)
        self.assertTrue(clock.is_control_tick(0))
        self.assertTrue(clock.is_observation_tick(0))
        self.assertFalse(clock.is_control_tick(1))


if __name__ == "__main__":
    unittest.main()
