"""Development-only timestep sensitivity of upstream AH-1S demonstration.

At h, h/2, h/4 the physics timestep changes but the observation clock
remains 0.15s. No controller gains are retuned, and the stock script/AFCS
remain active. This does not validate fixed-position hover.
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

BASE_DT = 0.0075
SAMPLE_S = 0.15
DURATION_S = 45.0
STEPS = (1, 2, 4)
PROPERTY_UNITS = {
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
ASSETS = (
    "aircraft/ah1s/ah1s.xml",
    "aircraft/ah1s/reset00.xml",
    "aircraft/ah1s/Systems/rotor_control.xml",
    "aircraft/ah1s/Systems/trim_control.xml",
    "systems/afcs.xml",
    "scripts/ah1s_flight_test.xml",
)


def _run(factor: int):
    dt = BASE_DT / factor
    ticks = round(SAMPLE_S / dt)
    if abs(ticks * dt - SAMPLE_S) > 1e-10:
        raise RuntimeError("observation and integrator clocks not commensurate")
    f = jsbsim.FGFDMExec(None)
    f.set_debug_level(0)
    root = Path(f.get_root_dir())
    # Per JSBSim's load_script Python binding, the nonzero second argument
    # overrides the script timestep for this instance.
    if not f.load_script(str(root / "scripts/ah1s_flight_test.xml"), dt):
        raise RuntimeError("unable to load stock flight test with requested dt")
    if abs(f.get_delta_t() - dt) > 1e-10:
        raise RuntimeError("backend did not apply requested integration dt")
    f.disable_output()
    if not f.run_ic():
        raise RuntimeError("run_ic failed")
    if any(name not in f.query_property_catalog(name)
           for name, _ in PROPERTY_UNITS.values()):
        raise RuntimeError("required telemetry absent")

    assets = {name: hashlib.sha256((root / name).read_bytes()).hexdigest()
              for name in ASSETS}
    samples = []
    for observation in range(round(DURATION_S / SAMPLE_S) + 1):
        if observation > 0:
            for _ in range(ticks):
                if not f.run():
                    raise RuntimeError("simulator stopped early")
        physical_time = observation * SAMPLE_S
        if abs(f.get_sim_time() - physical_time) > 2e-6:
            raise RuntimeError("physical sample clock slipped")
        row = {"time_s": physical_time}
        for key, (prop, scale) in PROPERTY_UNITS.items():
            value = float(f[prop]) * scale
            if not math.isfinite(value):
                raise RuntimeError("nonfinite physics state: " + prop)
            row[key] = value
        samples.append(row)
    return {"dt_s": dt, "steps": factor * round(DURATION_S / BASE_DT),
            "asset_sha256": assets, "trace": samples}


def _write(path: Path, obj: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8",
                                         dir=path.parent, prefix=path.name + ".",
                                         suffix=".tmp", delete=False) as stream:
            tmp = Path(stream.name)
            json.dump(obj, stream, sort_keys=True, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp, path)
    finally:
        if tmp is not None:
            tmp.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    results = {}
    failed = False
    for factor in STEPS:
        try:
            results[str(factor)] = {"status": "OK", **_run(factor)}
        except Exception as ex:
            failed = True
            results[str(factor)] = {"status": "UNRESOLVED",
                                    "error_type": type(ex).__name__,
                                    "reason": str(ex)}
    comparisons = {}
    if not failed:
        sha = results["1"]["asset_sha256"]
        for factor in ("2", "4"):
            if results[factor]["asset_sha256"] != sha:
                comparisons[factor] = {"status": "UNRESOLVED",
                                       "reason": "model_asset_changed"}
                failed = True
            else:
                comparisons[factor] = compare_traces(
                    results["1"]["trace"], results[factor]["trace"],
                    expected_period_s=SAMPLE_S)
                if comparisons[factor]["status"] != "DESCRIPTIVE_ONLY":
                    failed = True

    report = {
        "status": "UNRESOLVED" if failed else "DESCRIPTIVE_NUMERICAL_SENSITIVITY",
        "backend": "JSBSim",
        "version": jsbsim.__version__,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "model": "ah1s",
        "script": "ah1s_flight_test.xml",
        "script_variant": 1,
        "observation_period_s": SAMPLE_S,
        "duration_s": DURATION_S,
        "runs": results,
        "comparison_to_h": comparisons,
        "limitations": (
            "Stock scripted flight is not trimmed stationary hover; this "
            "only compares integration timesteps on one deterministic "
            "scenario. No convergence tolerance, cross-platform fidelity "
            "or scientific acceptance threshold has been established."
        ),
    }
    _write(args.output, report)
    print(json.dumps({
        "status": report["status"],
        "steps_by_factor": {k: r.get("steps") for k, r in results.items()},
        "comparisons": comparisons,
        "reproducible_output": str(args.output),
        "limitations": report["limitations"],
    }, indent=2))
    if failed:
        raise SystemExit("Timestep analysis unresolved; see evidence JSON")


if __name__ == "__main__":
    main()
