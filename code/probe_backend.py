"""Reproducible JSBSim feasibility probe, not a validated hover experiment."""
import argparse
import hashlib
import json
import math
import os
import platform
import tempfile
import time
from pathlib import Path

import jsbsim

from heli_lib.hover_metrics import screen_hover_window

PROPERTIES = [
    "position/h-agl-ft",
    "attitude/phi-rad",
    "attitude/theta-rad",
    "velocities/u-fps",
    "velocities/v-fps",
    "velocities/w-fps",
    "position/distance-from-start-lat-mt",
    "position/distance-from-start-lon-mt",
    "propulsion/engine/rotor-rpm",
]


def _write_json_atomically(path: Path, value: object) -> None:
    """Avoid treating partially written outputs as completed evidence."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent,
            prefix=path.name + ".", suffix=".tmp", delete=False
        ) as stream:
            temporary = Path(stream.name)
            stream.write(json.dumps(value, indent=2) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def run(seconds: float):
    f = jsbsim.FGFDMExec(None)
    f.set_debug_level(0)
    root = Path(f.get_root_dir())
    if not f.load_script(str(root / "scripts/ah1s_flight_test.xml")):
        raise RuntimeError("Could not load upstream helicopter script")
    f.disable_output()
    if not f.run_ic():
        raise RuntimeError("Initialization failed")
    for property_name in PROPERTIES:
        if property_name not in f.query_property_catalog(property_name):
            raise RuntimeError("Missing JSBSim property: " + property_name)
    rows = []
    start = time.perf_counter()
    while f.get_sim_time() < seconds:
        if not f.run():
            raise RuntimeError("Backend stopped early")
        row = [f.get_sim_time()] + [f[x] for x in PROPERTIES]
        if not all(math.isfinite(x) for x in row):
            raise RuntimeError("Nonfinite state")
        rows.append(row)
    assets = {}
    for folder in ("aircraft", "engine", "systems", "scripts"):
        for asset in sorted((root / folder).rglob("*.xml")):
            assets[str(asset.relative_to(root))] = hashlib.sha256(
                asset.read_bytes()
            ).hexdigest()
    return rows, time.perf_counter() - start, assets


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--seconds", type=float, default=60)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    if not math.isfinite(a.seconds) or a.seconds <= 0:
        p.error("seconds must be positive and finite")

    rows, elapsed, assets = run(a.seconds)
    replay, _, assets2 = run(a.seconds)
    if assets != assets2:
        raise RuntimeError("Model assets changed between runs")

    properties = ["simulation/sim-time-sec"] + PROPERTIES
    report = {
        "status": "feasibility_only",
        "backend": "JSBSim",
        "version": jsbsim.__version__,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "script": "ah1s_flight_test.xml",
        "script_variant": 1,
        "simulated_seconds": rows[-1][0],
        "steps": len(rows),
        "wall_seconds": elapsed,
        "exact_fresh_instance_replay": rows == replay,
        "properties": properties,
        "final_state": rows[-1],
        "asset_sha256": assets,
        "trajectory_sha256": hashlib.sha256(
            json.dumps(rows).encode()
        ).hexdigest(),
        "hover_screen": screen_hover_window(properties, rows),
        "limitations": (
            "Upstream scripted flight, not fixed-position hover validation. "
            "Stationarity candidate screen is exploratory; no scientifically "
            "validated controller, fault injection or failure outcome."
        ),
    }
    _write_json_atomically(a.output, report)
    _write_json_atomically(a.output.with_suffix(".trajectory.json"), rows)
    print(json.dumps(
        {k: v for k, v in report.items() if k != "asset_sha256"},
        indent=2,
    ))
    if rows != replay:
        raise SystemExit("Replay differs")


if __name__ == "__main__":
    main()
