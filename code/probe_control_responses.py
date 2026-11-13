"""Read-only research probe of AH-1S control responses from fresh instances.

This script performs short *open-loop* perturbations after the stock flight
demonstration has already lifted off. It neither establishes trim nor runs a
position-hold controller; scripted events and AFCS remain active.

Results MUST NOT be represented as control sign calibration, physical aircraft
validation or a publishable failure-scenario experiment.
"""
import argparse
import hashlib
import json
import math
import os
import platform
import tempfile
from pathlib import Path

import jsbsim

from heli_lib.control_response import PRIMARY_READOUTS, classify_pair

WARMUP_S = 45.0
RESPONSE_S = 2.0
DELTA = 0.06

CHANNELS = {
    "collective": "fcs/collective-cmd-norm",
    "longitudinal": "fcs/elevator-cmd-norm",
    "lateral": "fcs/aileron-cmd-norm",
    "pedal": "fcs/rudder-cmd-norm",
}
READOUTS = (
    "simulation/sim-time-sec",
    "position/h-agl-ft",
    "position/distance-from-start-lat-mt",
    "position/distance-from-start-lon-mt",
    "attitude/phi-rad",
    "attitude/theta-rad",
    "attitude/psi-rad",
    "velocities/u-fps",
    "velocities/v-fps",
    "velocities/w-fps",
    "velocities/p-aero-rad_sec",
    "velocities/q-aero-rad_sec",
    "velocities/r-aero-rad_sec",
    "propulsion/engine/rotor-rpm",
    "propulsion/engine/collective-ctrl-rad",
    "propulsion/engine/longitudinal-ctrl-rad",
    "propulsion/engine/lateral-ctrl-rad",
    "propulsion/engine[1]/antitorque-ctrl-rad",
) + tuple(CHANNELS.values())

ACTUATORS = {
    "collective": "propulsion/engine/collective-ctrl-rad",
    "longitudinal": "propulsion/engine/longitudinal-ctrl-rad",
    "lateral": "propulsion/engine/lateral-ctrl-rad",
    "pedal": "propulsion/engine[1]/antitorque-ctrl-rad",
}

ASSET_PATHS = (
    "aircraft/ah1s/ah1s.xml",
    "aircraft/ah1s/reset00.xml",
    "aircraft/ah1s/Systems/rotor_control.xml",
    "aircraft/ah1s/Systems/trim_control.xml",
    "systems/afcs.xml",
    "scripts/ah1s_flight_test.xml",
)


def _record(f) -> dict:
    state = {key: float(f[key]) for key in READOUTS}
    if not all(math.isfinite(x) for x in state.values()):
        raise RuntimeError("nonfinite simulator readout")
    return state


def _fresh_run(channel: str | None = None, sign: int = 0) -> dict:
    f = jsbsim.FGFDMExec(None)
    f.set_debug_level(0)
    root = Path(f.get_root_dir())
    if not f.load_script(str(root / "scripts/ah1s_flight_test.xml")):
        raise RuntimeError("cannot load pinned stock AH-1S script")
    f.disable_output()
    if not f.run_ic():
        raise RuntimeError("cannot initialize AH-1S")
    for key in READOUTS:
        if key not in f.query_property_catalog(key):
            raise RuntimeError("missing expected model readout: " + key)

    # The script's time step, initial state and events are not altered.
    dt = f.get_delta_t()
    while f.get_sim_time() < WARMUP_S - dt / 2:
        if not f.run():
            raise RuntimeError("warmup run stopped")
    before = _record(f)
    if abs(before["simulation/sim-time-sec"] - WARMUP_S) > dt:
        raise RuntimeError("warmup time not aligned with script integrator")

    if channel is not None:
        key = CHANNELS[channel]
        value = before[key] + sign * DELTA
        if (value < 0 or value > 1) if channel == "collective" else (abs(value) > 1):
            raise RuntimeError("pilot-control perturbation exceeds normalized range")
        f[key] = value
        readback = f[key]
        if abs(readback - value) > 1e-10:
            raise RuntimeError("control command was not accepted")
    else:
        readback = None

    end_time = WARMUP_S + RESPONSE_S
    while f.get_sim_time() < end_time - dt / 2:
        if not f.run():
            raise RuntimeError("response trial stopped early")
    after = _record(f)
    if abs(after["simulation/sim-time-sec"] - end_time) > dt:
        raise RuntimeError("response time not aligned with script integrator")

    hashes = {}
    for path in ASSET_PATHS:
        asset = root / path
        if not asset.is_file():
            raise RuntimeError("model asset missing: " + path)
        hashes[path] = hashlib.sha256(asset.read_bytes()).hexdigest()
    return {
        "before": before,
        "after": after,
        "readback": readback,
        "dt_s": dt,
        "asset_sha256": hashes,
    }


def _atomic_json(path: Path, report: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", dir=path.parent, encoding="utf-8",
            prefix=path.name + ".", suffix=".tmp", delete=False,
        ) as stream:
            temporary = Path(stream.name)
            stream.write(json.dumps(report, indent=2, sort_keys=True) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def run_experiment() -> dict:
    baseline = _fresh_run()
    repeat = _fresh_run()
    if baseline != repeat:
        raise RuntimeError("fresh-instance baseline replay mismatch")
    cases = {}
    for channel, prop in CHANNELS.items():
        negative, positive = _fresh_run(channel, -1), _fresh_run(channel, +1)
        for case in (negative, positive):
            if case["asset_sha256"] != baseline["asset_sha256"]:
                raise RuntimeError("model assets changed between simulations")
            if case["dt_s"] != baseline["dt_s"]:
                raise RuntimeError("integrator time step changed")
            if case["before"] != baseline["before"]:
                raise RuntimeError("trial initial state differs from baseline")
        measured = PRIMARY_READOUTS[channel]
        readout = classify_pair(
            baseline["after"][measured],
            negative["after"][measured],
            positive["after"][measured],
            DELTA,
        )
        actuator = ACTUATORS[channel]
        actuator_minus = negative["after"][actuator] - baseline["after"][actuator]
        actuator_plus = positive["after"][actuator] - baseline["after"][actuator]
        # A pilot command can be overwritten by stock script automation.
        # Actuator differences alone are NOT proof of independent sign.
        actuator_reached = abs(actuator_minus) > 1e-8 or abs(actuator_plus) > 1e-8
        cases[channel] = {
            "command_property": prop,
            "primary_readout": measured,
            "actuator_property": actuator,
            "command_at_warmup": baseline["before"][prop],
            "readback_minus": negative["readback"],
            "readback_plus": positive["readback"],
            "actual_command_at_end": {
                "baseline": baseline["after"][prop],
                "minus": negative["after"][prop],
                "plus": positive["after"][prop],
            },
            "actuator_difference_minus": actuator_minus,
            "actuator_difference_plus": actuator_plus,
            "actuator_reached": actuator_reached,
            "readout_difference": readout,
            "after_minus": negative["after"],
            "after_plus": positive["after"],
        }
    return {
        "status": "EXPLORATORY_CONTROL_RESPONSE_ONLY",
        "backend": "JSBSim",
        "version": jsbsim.__version__,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "script": "ah1s_flight_test.xml",
        "script_variant": 1,
        "warmup_seconds": WARMUP_S,
        "response_seconds": RESPONSE_S,
        "perturbation_norm": DELTA,
        "integration_dt_seconds": baseline["dt_s"],
        "fresh_instance_baseline_replay": True,
        "asset_sha256": baseline["asset_sha256"],
        "baseline_before": baseline["before"],
        "baseline_after": baseline["after"],
        "cases": cases,
        "limitations": (
            "Stock scripted flight and onboard AFCS remain active. "
            "This is not a trim point, a control-sign verification, "
            "a stationary hover demonstration, or real-aircraft validation. "
            "Apparent control sensitivities are exploratory only."
        ),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    report = run_experiment()
    _atomic_json(arguments.output, report)
    print(json.dumps({
        "status": report["status"],
        "backend": report["backend"],
        "version": report["version"],
        "dt_s": report["integration_dt_seconds"],
        "fresh_instance_baseline_replay": report["fresh_instance_baseline_replay"],
        "channels": {
            key: {
                "actuator_reached": case["actuator_reached"],
                "response": case["readout_difference"],
                "actuator_difference_minus": case["actuator_difference_minus"],
                "actuator_difference_plus": case["actuator_difference_plus"],
                "command_at_end": case["actual_command_at_end"],
            }
            for key, case in report["cases"].items()
        },
    }, indent=2))


if __name__ == "__main__":
    main()
