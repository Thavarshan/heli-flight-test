"""Interpret pre-validation paired pilot-control perturbations.

These are local script-state sensitivities only, not independently verified
control signs, trim gradients, aircraft fidelity or stable hover.
"""
import math

# The chosen pairs are plausible readouts, not guaranteed uncoupled axes.
PRIMARY_READOUTS = {
    "collective": "position/h-agl-ft",
    "longitudinal": "velocities/q-aero-rad_sec",
    "lateral": "velocities/p-aero-rad_sec",
    "pedal": "velocities/r-aero-rad_sec",
}

def classify_pair(base: float, minus: float, plus: float, delta: float) -> dict:
    """Classify the primary readout's finite local differences.

    Only call this after checking the command actually reaches the actuator.
    NONMONOTONE and UNRESOLVED are not evidence of reversed control.
    """
    if not all(math.isfinite(v) for v in (base, minus, plus, delta)):
        return {"status": "UNRESOLVED", "reason": "nonfinite_input"}
    if delta <= 0:
        raise ValueError("delta must be positive")
    lower, upper = minus - base, plus - base
    slope = (plus - minus) / (2 * delta)
    if abs(lower) <= 1e-8 and abs(upper) <= 1e-8:
        category = "NO_MEASURABLE_RESPONSE"
    elif lower < -1e-8 and upper > 1e-8:
        category = "POSITIVE_MONOTONE"
    elif lower > 1e-8 and upper < -1e-8:
        category = "NEGATIVE_MONOTONE"
    else:
        category = "NONMONOTONE_OR_DRIFT"
    return {
        "status": category,
        "minus_difference": lower,
        "plus_difference": upper,
        "central_difference_per_normalized_command": slope,
    }
