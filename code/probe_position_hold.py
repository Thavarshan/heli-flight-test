"""Exploratory *closed-loop* position-feedback trial against stock script.

This is a development pilot, NOT a proven stable-hover controller. The
existing AH-1S AFCS remains enabled; control signs are hypotheses and the
state is directly observed rather than delivered by a physical sensor.
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

from heli_lib.hover_controller import FT_TO_M, compute_hold_commands

WARMUP_S = 45.0
RUN_S = 25.0
CONTROL_STEPS = 20  # 20 * stock integration dt 0.0075 = 0.15 seconds
KEYS = {
    "collective": "fcs/collective-cmd-norm",
    "longitudinal": "fcs/elevator-cmd-norm",
    "lateral": "fcs/aileron-cmd-norm",
    "pedal": "fcs/rudder-cmd-norm",
}
STATE_KEYS = (
    "position/h-agl-ft",
    "position/distance-from-start-lat-mt",
    "position/distance-from-start-lon-mt",
    "attitude/psi-rad",
    "velocities/u-fps",
    "velocities/v-fps",
    "velocities/h-dot-fps",
    "velocities/p-aero-rad_sec",
    "velocities/q-aero-rad_sec",
    "velocities/r-aero-rad_sec",
    "propulsion/engine/rotor-rpm",
)
MODEL_FILES = (
    "aircraft/ah1s/ah1s.xml",
    "aircraft/ah1s/reset00.xml",
    "aircraft/ah1s/Systems/rotor_control.xml",
    "systems/afcs.xml",
    "scripts/ah1s_flight_test.xml",
)


def _state(f) -> dict:
    read = {name: float(f[name]) for name in STATE_KEYS}
    if not all(math.isfinite(v) for v in read.values()):
        raise RuntimeError("nonfinite simulator state")
    return {
        "north_m": read["position/distance-from-start-lat-mt"],
        "east_m": read["position/distance-from-start-lon-mt"],
        "agl_m": read["position/h-agl-ft"] * FT_TO_M,
        "psi_rad": read["attitude/psi-rad"],
        "u_mps": read["velocities/u-fps"] * FT_TO_M,
        "v_mps": read["velocities/v-fps"] * FT_TO_M,
        "climb_mps": read["velocities/h-dot-fps"] * FT_TO_M,
        "p_rad_s": read["velocities/p-aero-rad_sec"],
        "q_rad_s": read["velocities/q-aero-rad_sec"],
        "r_rad_s": read["velocities/r-aero-rad_sec"],
        "rotor_rpm": read["propulsion/engine/rotor-rpm"],
    }


def _run(with_control: bool) -> dict:
    f = jsbsim.FGFDMExec(None)
    f.set_debug_level(0)
    root = Path(f.get_root_dir())
    if not f.load_script(str(root / "scripts/ah1s_flight_test.xml")):
        raise RuntimeError("could not load AH-1S stock script")
    f.disable_output()
    if not f.run_ic():
        raise RuntimeError("AH-1S initialization failed")
    for name in STATE_KEYS + tuple(KEYS.values()):
        if name not in f.query_property_catalog(name):
            raise RuntimeError("missing expected model property: " + name)
    dt = f.get_delta_t()
    if abs(dt * CONTROL_STEPS - 0.15) > 1e-9:
        raise RuntimeError("controller period must equal 0.15s at stock step")
    while f.get_sim_time() < WARMUP_S - dt/2:
        if not f.run():
            raise RuntimeError("script stopped during warmup")
    if abs(f.get_sim_time() - WARMUP_S) > dt:
        raise RuntimeError("warmup timestamp error")
    initial = _state(f)
    nominal = {name: float(f[prop]) for name, prop in KEYS.items()}
    target = {name: initial[name] for name in ("north_m", "east_m", "agl_m")}
    trace = []
    command_overwrites = 0
    commands = None
    n_steps = round(RUN_S / dt)
    for i in range(n_steps):
        if with_control and i % CONTROL_STEPS == 0:
            commands = compute_hold_commands(_state(f), target, nominal)
        if with_control:
            for name, prop in KEYS.items():
                # Set every JSBSim step to minimize stock script-ramp interference;
                # never assume that this fully decouples stock scripting.
                f[prop] = commands[name]
        if not f.run():
            raise RuntimeError("script stopped during position-hold pilot")
        if with_control:
            if any(abs(f[prop] - commands[name]) > 1e-5
                   for name, prop in KEYS.items()):
                command_overwrites += 1
        if (i + 1) % CONTROL_STEPS == 0:
            trace.append({"time_s": f.get_sim_time(),
                          "state": _state(f),
                          "command": dict(commands) if with_control else None})
    if not trace:
        raise RuntimeError("no pilot samples")
    hashes = {name: hashlib.sha256((root/name).read_bytes()).hexdigest()
              for name in MODEL_FILES}
    end = trace[-1]["state"]
    horizontal_dist = math.hypot(end["north_m"] - target["north_m"],
                                 end["east_m"] - target["east_m"])
    # Use sample-level descriptive comparisons; no frozen scientific thresholds.
    errors = [math.hypot(t["state"]["north_m"] - target["north_m"],
                         t["state"]["east_m"] - target["east_m"]) for t in trace]
    return {
        "initial": initial, "nominal_commands": nominal,
        "target": target, "trace": trace,
        "final_horizontal_error_m": horizontal_dist,
        "sampled_rms_horizontal_error_m": math.sqrt(sum(e*e for e in errors)/len(errors)),
        "max_sampled_horizontal_error_m": max(errors),
        "last_agl_m": end["agl_m"],
        "min_sampled_agl_m": min(t["state"]["agl_m"] for t in trace),
        "control_steps": CONTROL_STEPS,
        "command_overwrite_step_count": command_overwrites,
        "asset_sha256": hashes,
        "dt_s": dt,
    }


def _atomic_save(path: Path, object_: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent,
            prefix=path.name + ".", suffix=".tmp", delete=False
        ) as stream:
            temp = Path(stream.name)
            stream.write(json.dumps(object_, indent=2, sort_keys=True) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, path)
    finally:
        if temp is not None:
            temp.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    neutral = _run(False)
    controlled = _run(True)
    repeat = _run(True)
    if controlled != repeat:
        raise RuntimeError("closed-loop trace did not replay exactly")
    if neutral["initial"] != controlled["initial"]:
        raise RuntimeError("initial state differs across comparison arms")
    if neutral["asset_sha256"] != controlled["asset_sha256"]:
        raise RuntimeError("aircraft assets differ across comparison arms")
    report = {
        "status": "EXPLORATORY_POSITION_FEEDBACK_ONLY",
        "backend": "JSBSim",
        "backend_version": jsbsim.__version__,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "warmup_seconds": WARMUP_S,
        "feedback_seconds": RUN_S,
        "controller_period_s": CONTROL_STEPS * controlled["dt_s"],
        "fresh_instance_closed_loop_replay": True,
        "stock_script_and_afcs_active": True,
        "baseline": neutral,
        "controlled": controlled,
        "limitations": (
            "Initial state is the moving stock-script condition at 45 seconds, "
            "not a validated trim. Perfect-state feedback and heuristic gains "
            "are unvalidated. CI success only means a deterministic finite "
            "experiment, not improved or stable fixed-position hover."
        ),
    }
    _atomic_save(args.output, report)
    print(json.dumps({
        "status": report["status"],
        "exact_fresh_instance_replay": True,
        "stock_script_and_afcs_active": True,
        "baseline_final_horizontal_error_m": neutral["final_horizontal_error_m"],
        "feedback_final_horizontal_error_m": controlled["final_horizontal_error_m"],
        "baseline_sampled_rms_horizontal_error_m": neutral["sampled_rms_horizontal_error_m"],
        "feedback_sampled_rms_horizontal_error_m": controlled["sampled_rms_horizontal_error_m"],
        "baseline_min_sampled_agl_m": neutral["min_sampled_agl_m"],
        "feedback_min_sampled_agl_m": controlled["min_sampled_agl_m"],
        "script_command_override_steps": controlled["command_overwrite_step_count"],
        "limitations": report["limitations"],
    }, indent=2))


if __name__ == "__main__":
    main()
