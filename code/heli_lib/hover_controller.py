"""Development-only helicopter position-hold controller proposal.

Uses perfect simulator state and assumed pilot-control directions inferred
from an exploratory transient probe. It is NOT tuned or validated for hover.
All positions use JSBSim north/east displacement in metres; velocities use
body-forward/right ft/s converted to m/s; altitude AGL is feet converted to m.
"""
import math
from dataclasses import dataclass

FT_TO_M = 0.3048

@dataclass(frozen=True)
class HoldGains:
    horizontal_position: float = 0.012
    horizontal_speed: float = 0.065
    altitude_position: float = 0.012
    vertical_speed: float = 0.020
    cyclic_limit: float = 0.14
    collective_limit: float = 0.14


def _clip(x: float, lo: float, hi: float) -> float:
    return min(hi, max(lo, x))


def compute_hold_commands(
    state: dict[str, float],
    target: dict[str, float],
    nominal: dict[str, float],
    gains: HoldGains = HoldGains(),
) -> dict[str, float]:
    """Propose bounded inputs, leaving rudder under existing yaw AFCS.

    Sign choices are a *development hypothesis*, not independent control-
    direction validation. Do not deploy to real hardware.
    """
    fields = ("north_m", "east_m", "agl_m", "psi_rad", "u_mps", "v_mps",
              "climb_mps")
    if any(k not in state for k in fields):
        raise ValueError("state is missing a required unit-declared field")
    if any(k not in target for k in ("north_m", "east_m", "agl_m")):
        raise ValueError("target is missing a position component")
    if any(k not in nominal for k in ("collective", "longitudinal", "lateral", "pedal")):
        raise ValueError("nominal controls are incomplete")
    values = list(state.values()) + list(target.values()) + list(nominal.values())
    if not all(isinstance(v, (int, float)) and math.isfinite(v) for v in values):
        raise ValueError("nonfinite or nonnumeric control input")
    if any((not math.isfinite(v) or v <= 0) for v in vars(gains).values()):
        raise ValueError("gains must be positive and finite")

    north_err = state["north_m"] - target["north_m"]
    east_err = state["east_m"] - target["east_m"]
    psi = state["psi_rad"]
    # NED horizontal direction transformed to body-forward/right.
    forward_err = math.cos(psi) * north_err + math.sin(psi) * east_err
    right_err = -math.sin(psi) * north_err + math.cos(psi) * east_err

    d_long = (-gains.horizontal_position * forward_err
              -gains.horizontal_speed * state["u_mps"])
    d_lat = (-gains.horizontal_position * right_err
             -gains.horizontal_speed * state["v_mps"])
    d_col = (gains.altitude_position * (target["agl_m"] - state["agl_m"])
             -gains.vertical_speed * state["climb_mps"])

    return {
        "collective": _clip(nominal["collective"] +
                            _clip(d_col, -gains.collective_limit, gains.collective_limit),
                            0.0, 1.0),
        "longitudinal": _clip(nominal["longitudinal"] +
                              _clip(d_long, -gains.cyclic_limit, gains.cyclic_limit),
                              -1.0, 1.0),
        "lateral": _clip(nominal["lateral"] +
                         _clip(d_lat, -gains.cyclic_limit, gains.cyclic_limit),
                         -1.0, 1.0),
        "pedal": nominal["pedal"],
    }
