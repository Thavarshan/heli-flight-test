"""Exploratory stationarity screen for JSBSim helicopter trajectories.

A passing screen is NOT validated hover, trim, or aircraft fidelity. The
flight model, control signs, perturbations, and timestep convergence must
be validated separately before scientific evaluation.
"""
import math
from collections.abc import Sequence

FT_TO_M = 0.3048
REQUIRED = (
    "simulation/sim-time-sec",
    "position/h-agl-ft",
    "position/distance-from-start-lat-mt",
    "position/distance-from-start-lon-mt",
    "attitude/phi-rad",
    "attitude/theta-rad",
    "velocities/u-fps",
    "velocities/v-fps",
    "velocities/w-fps",
    "propulsion/engine/rotor-rpm",
)
# Development-only screening limits, NOT frozen scientific failure thresholds.
LIMITS = {
    "max_body_speed_mps": 1.0,
    "max_horizontal_excursion_m": 3.0,
    "altitude_span_m": 2.0,
    "max_abs_tilt_deg": 10.0,
    "min_agl_m": 5.0,
    "min_rotor_rpm": 1.0,
}


def _unresolved(reason: str, **details: object) -> dict:
    return {"status": "UNRESOLVED", "reason": reason, **details}


def screen_hover_window(
    properties: Sequence[str],
    rows: Sequence[Sequence[float]],
    *,
    window_s: float = 20.0,
    max_sample_gap_s: float = 1.0,
) -> dict:
    """Screen the final window for approximate stationarity in declared units.

    Uses body-frame velocity magnitude (rotation-invariant), AGL height,
    JSBSim north/east displacement-from-start differences, roll/pitch,
    and main rotor RPM. A passing result is a *candidate* only.
    """
    if (not math.isfinite(window_s) or window_s <= 0
            or not math.isfinite(max_sample_gap_s) or max_sample_gap_s <= 0):
        raise ValueError("window and maximum sample gap must be positive and finite")
    if len(set(properties)) != len(properties):
        return _unresolved("duplicate_property_names")
    missing = sorted(set(REQUIRED) - set(properties))
    if missing:
        return _unresolved("missing_properties", missing=missing)
    if not rows:
        return _unresolved("empty_trajectory")

    names = {name: properties.index(name) for name in REQUIRED}
    samples = []
    previous_time = -math.inf
    for index, row in enumerate(rows):
        if len(row) != len(properties):
            return _unresolved("invalid_row_width", row_index=index)
        try:
            values = [float(v) for v in row]
        except (TypeError, ValueError, OverflowError):
            return _unresolved("non_numeric_value", row_index=index)
        if not all(math.isfinite(v) for v in values):
            return _unresolved("nonfinite_value", row_index=index)
        t = values[names["simulation/sim-time-sec"]]
        if t <= previous_time:
            return _unresolved("non_increasing_timestamps", row_index=index)
        previous_time = t
        samples.append(values)

    end = samples[-1][names["simulation/sim-time-sec"]]
    start = end - window_s
    if start < 0:
        return _unresolved("insufficient_duration", available_seconds=end, required_seconds=window_s)
    window = [row for row in samples if row[names["simulation/sim-time-sec"]] >= start]
    if len(window) < 2:
        return _unresolved("insufficient_window_samples")
    first_time = window[0][names["simulation/sim-time-sec"]]
    if first_time - start > max_sample_gap_s:
        return _unresolved("window_start_not_covered", first_time=first_time)
    times = [row[names["simulation/sim-time-sec"]] for row in window]
    if any(b - a > max_sample_gap_s for a, b in zip(times, times[1:])):
        return _unresolved("sample_gap_exceeds_limit")

    def series(name: str) -> list[float]:
        return [row[names[name]] for row in window]

    u, v, w = (series("velocities/" + axis + "-fps") for axis in "uvw")
    speed = max(math.sqrt(a*a + b*b + c*c) for a, b, c in zip(u, v, w)) * FT_TO_M
    north = series("position/distance-from-start-lat-mt")
    east = series("position/distance-from-start-lon-mt")
    excursion = max(math.hypot(n - north[0], e - east[0])
                    for n, e in zip(north, east))
    altitude = [h * FT_TO_M for h in series("position/h-agl-ft")]
    tilt = max(max(abs(a), abs(b)) for a, b in zip(
        series("attitude/phi-rad"), series("attitude/theta-rad"))) * 180 / math.pi
    rotor = series("propulsion/engine/rotor-rpm")
    metrics = {
        "max_body_speed_mps": speed,
        "max_horizontal_excursion_m": excursion,
        "altitude_span_m": max(altitude) - min(altitude),
        "max_abs_tilt_deg": tilt,
        "min_agl_m": min(altitude),
        "min_rotor_rpm": min(rotor),
    }
    criteria = {key: (metrics[key] >= value if key.startswith("min_")
                      else metrics[key] <= value)
                for key, value in LIMITS.items()}
    return {
        "status": "PASS_CANDIDATE" if all(criteria.values()) else "FAIL_CANDIDATE",
        "window_s": window_s,
        "samples": len(window),
        "thresholds": dict(LIMITS),
        "criteria": criteria,
        "metrics": metrics,
        "limitations": "Exploratory screen only; neither model validation nor fixed-position closed-loop hover.",
    }
