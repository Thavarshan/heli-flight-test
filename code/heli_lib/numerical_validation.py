"""Numerical-grid comparisons; these are not aircraft-model validation.

Every trace uses one shared physical-time observation clock. Mismatch, missing
telemetry and backend errors must not be interpreted as controller violations.
"""
import math
from collections.abc import Mapping, Sequence

UNITS = {
    "north_m": "m",
    "east_m": "m",
    "agl_m": "m",
    "phi_rad": "rad",
    "theta_rad": "rad",
    "psi_rad": "rad",
    "u_mps": "m/s",
    "v_mps": "m/s",
    "w_mps": "m/s",
    "rotor_rpm": "rpm",
}


def compare_traces(
    reference: Sequence[Mapping[str, float]],
    refined: Sequence[Mapping[str, float]],
    *,
    expected_period_s: float,
) -> dict:
    """Calculate aligned difference statistics, failing closed on bad traces."""
    if not math.isfinite(expected_period_s) or expected_period_s <= 0:
        raise ValueError("expected_period_s must be finite and positive")
    if len(reference) != len(refined) or len(reference) < 2:
        return {"status": "UNRESOLVED", "reason": "incompatible_trace_lengths"}
    keys = {"time_s", *UNITS}
    for label, trace in (("reference", reference), ("refined", refined)):
        previous = None
        for index, record in enumerate(trace):
            if set(record) != keys:
                return {"status": "UNRESOLVED", "reason": "missing_or_extra_columns",
                        "trace": label, "row": index}
            try:
                values = {key: float(record[key]) for key in keys}
            except (ValueError, TypeError, OverflowError):
                return {"status": "UNRESOLVED", "reason": "nonnumeric_input",
                        "trace": label, "row": index}
            if not all(math.isfinite(v) for v in values.values()):
                return {"status": "UNRESOLVED", "reason": "nonfinite_input",
                        "trace": label, "row": index}
            instant = values["time_s"]
            if previous is not None and (instant <= previous or
                    not math.isclose(instant - previous, expected_period_s,
                                     rel_tol=0, abs_tol=1e-6)):
                return {"status": "UNRESOLVED", "reason": "invalid_observation_clock",
                        "trace": label, "row": index}
            previous = instant
    if any(not math.isclose(float(a["time_s"]), float(b["time_s"]),
                            rel_tol=0, abs_tol=1e-6)
           for a, b in zip(reference, refined)):
        return {"status": "UNRESOLVED", "reason": "unaligned_physical_timestamps"}

    diffs = {
        key: [float(a[key]) - float(b[key]) for a, b in zip(reference, refined)]
        for key in UNITS
    }
    return {"status": "DESCRIPTIVE_ONLY", "samples": len(reference),
            "units": dict(UNITS),
            "max_abs_difference": {
                k: max(abs(v) for v in values) for k, values in diffs.items()
            },
            "rms_difference": {
                k: math.sqrt(sum(v*v for v in values) / len(values))
                for k, values in diffs.items()
            },
            "limitation": (
                "Pointwise numerical sensitivity only; no tolerances are frozen, "
                "and closeness does not establish trim or physical validity."
            )}
