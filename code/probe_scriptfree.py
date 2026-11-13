"""Script-free JSBSim AH-1S initialization feasibility test.

This is an intentionally *untrimmed* diagnostic. It loads the aircraft and
initial-condition XML directly, without executing any flight script events.
It never claims steady hover, control validity, or real-aircraft fidelity.
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

from heli_lib.numerical_validation import compare_traces

DT0 = 0.0075
SAMPLE_PERIOD = 0.15
DURATION = 4.5
MODEL_ASSETS = (
    "aircraft/ah1s/ah1s.xml",
    "aircraft/ah1s/reset00.xml",
    "aircraft/ah1s/Systems/rotor_control.xml",
    "aircraft/ah1s/Systems/trim_control.xml",
    "systems/afcs.xml",
)
READ = {
    "north_m": ("position/distance-from-start-lat-mt", 1.0),
    "east_m": ("position/distance-from-start-lon-mt", 1.0),
    "agl_m": ("position/h-agl-ft", 0.3048),
    "phi_rad": ("attitude/phi-rad", 1.0),
    "theta_rad": ("attitude/theta-rad", 1.0),
    "psi_rad": ("attitude/psi-rad", 1.0),
    "u_mps": ("velocities/u-fps", 0.3048),
    "v_mps": ("velocities/v-fps", 0.3048),
    "w_mps": ("velocities/w-fps", 0.3048),
    "rotor_rpm": ("propulsion/engine/rotor-rpm", 1.0),
}
CONTROL = {
    "fcs/collective-cmd-norm": .615,
    "fcs/elevator-cmd-norm": -.1558,
    "fcs/aileron-cmd-norm": .19095,
    "fcs/rudder-cmd-norm": .39,
    "fcs/rpm-governor-active-norm": 1.0,
    "fcs/adj/collective-profile": 0.0,
    "fcs/adj/center-sensitivity": 1.0,
}
# AGL target is deliberately above ground at init, *not* a trim state.
START_AGL_FT = 75.0


def run_trial(factor: int) -> dict:
    dt = DT0 / factor
    ticks = round(SAMPLE_PERIOD / dt)
    if not math.isclose(ticks * dt, SAMPLE_PERIOD, abs_tol=1e-10):
        raise RuntimeError("incompatible clock period")
    f = jsbsim.FGFDMExec(None)
    f.set_debug_level(0)
    root = Path(f.get_root_dir())
    if not f.load_model("ah1s"):
        raise RuntimeError("could not load AH-1S model independently")
    if not f.load_ic(str(root / "aircraft/ah1s/reset00.xml"), True):
        raise RuntimeError("could not load AH-1S initial condition")
    f.set_dt(dt)
    f["ic/h-agl-ft"] = START_AGL_FT
    f.disable_output()
    if not f.run_ic():
        raise RuntimeError("independent run_ic failed")
    if abs(f["position/h-agl-ft"] - START_AGL_FT) > 1:
        raise RuntimeError("initial airborne AGL was not applied")
    for key, value in CONTROL.items():
        if key not in f.query_property_catalog(key):
            raise RuntimeError("missing expected control: " + key)
        f[key] = value
    if any(prop not in f.query_property_catalog(prop)
           for prop, _ in READ.values()):
        raise RuntimeError("required telemetry missing")
    state = []
    for count in range(round(DURATION / SAMPLE_PERIOD)+1):
        if count:
            for _ in range(ticks):
                # Explicitly own the pilot controls; never use an event script.
                for name, val in CONTROL.items():
                    f[name] = val
                if not f.run():
                    raise RuntimeError("script-free simulation terminated")
        if abs(f.get_sim_time() - count*SAMPLE_PERIOD) > 1e-6:
            raise RuntimeError("simulator time drift")
        row = {"time_s": count*SAMPLE_PERIOD}
        for name, (prop, scale) in READ.items():
            value = float(f[prop]) * scale
            if not math.isfinite(value):
                raise RuntimeError("nonfinite simulator state "+prop)
            row[name] = value
        state.append(row)
    hashes = {key: hashlib.sha256((root/key).read_bytes()).hexdigest()
              for key in MODEL_ASSETS}
    return {
        "dt_s": dt,
        "samples": state,
        "assets_sha256": hashes,
        "min_agl_m": min(v["agl_m"] for v in state),
        "max_rotor_rpm": max(v["rotor_rpm"] for v in state),
    }


def save(path: Path, report: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = None
    try:
        with tempfile.NamedTemporaryFile("w", dir=path.parent, encoding="utf-8",
                                         prefix=path.name+".", suffix=".tmp",
                                         delete=False) as out:
            tmp = Path(out.name)
            json.dump(report, out, indent=2, sort_keys=True)
            out.write("\n")
            out.flush()
            os.fsync(out.fileno())
        os.replace(tmp, path)
    finally:
        if tmp is not None:
            tmp.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    trials = {}
    for factor in (1,2,4):
        try:
            trials[str(factor)] = {"status": "OK", **run_trial(factor)}
        except Exception as exc:
            trials[str(factor)] = {"status": "UNRESOLVED",
                                   "reason": type(exc).__name__ + ": " + str(exc)}
    base = trials["1"]
    comparisons = {}
    if all(t["status"] == "OK" for t in trials.values()):
        for key in ("2","4"):
            comparisons[key] = compare_traces(base["samples"], trials[key]["samples"],
                                             expected_period_s=SAMPLE_PERIOD)
    report = {
        "status": "SCRIPT_FREE_INITIALIZATION_DIAGNOSTIC" if comparisons else "UNRESOLVED",
        "backend_version": jsbsim.__version__,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "description": "Direct AH-1S aircraft+IC, artificial 75ft AGL start, no flight script.",
        "pilot_controls": CONTROL,
        "trials": trials,
        "comparison_to_h": comparisons,
        "limitations": (
            "Artificial untrimmed state, no validated rotor spin-up/torque "
            "or control authority. Even finite numerical differences do "
            "not establish hover, convergence or physical validity."
        ),
    }
    save(args.output, report)
    print(json.dumps({
        "status": report["status"],
        "trials": {k: {field: value for field, value in t.items()
                       if field in ("status","reason","dt_s","min_agl_m","max_rotor_rpm")}
                   for k,t in trials.items()},
        "comparison_to_h": {k: {"status": v["status"],
                                "max_north_error_m": v.get("max_abs_difference",{}).get("north_m"),
                                "max_agl_error_m": v.get("max_abs_difference",{}).get("agl_m")}
                            for k,v in comparisons.items()},
        "limitations": report["limitations"],
    }, indent=2))
    if report["status"] == "UNRESOLVED":
        raise SystemExit("Unresolved script-free backend diagnostic: see report")


if __name__ == "__main__":
    main()
