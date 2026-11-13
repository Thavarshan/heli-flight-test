"""Explicit physical-time clock for experimental control/sensor updates.

The control and observation periods are *physical seconds*, not fractions of
the integrator timestep. No floating-point modulo is used in integration.
"""
import math
from dataclasses import dataclass


@dataclass(frozen=True)
class SimulationClock:
    physics_dt_s: float
    control_period_s: float = 0.15
    observation_period_s: float = 0.15

    def __post_init__(self):
        for field in ("physics_dt_s", "control_period_s", "observation_period_s"):
            value = getattr(self, field)
            if not math.isfinite(value) or value <= 0:
                raise ValueError(field + " must be finite and positive")
        # Research protocol disallows nearest-tick aliasing: reject dt values
        # that cannot exactly represent the intended physical-time schedule.
        for period in (self.control_period_s, self.observation_period_s):
            tick_count = round(period / self.physics_dt_s)
            if tick_count < 1 or abs(period - tick_count * self.physics_dt_s) > 1e-10:
                raise ValueError("physics timestep cannot represent the declared clock")

    @property
    def control_ticks(self):
        return round(self.control_period_s / self.physics_dt_s)

    @property
    def observation_ticks(self):
        return round(self.observation_period_s / self.physics_dt_s)

    def is_control_tick(self, step: int) -> bool:
        if step < 0:
            raise ValueError("step cannot be negative")
        return step % self.control_ticks == 0

    def is_observation_tick(self, step: int) -> bool:
        if step < 0:
            raise ValueError("step cannot be negative")
        return step % self.observation_ticks == 0

    def time_s(self, step: int) -> float:
        if step < 0:
            raise ValueError("step cannot be negative")
        return step * self.physics_dt_s

    def ticks_for_duration(self, seconds: float) -> int:
        if not math.isfinite(seconds) or seconds < 0:
            raise ValueError("duration must be nonnegative and finite")
        n = round(seconds / self.physics_dt_s)
        if abs(n * self.physics_dt_s - seconds) > 1e-10:
            raise ValueError("duration must align with physics clock")
        return n
