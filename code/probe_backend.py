"""Reproducible feasibility probe, not a validated hover experiment."""
import argparse
import hashlib
import json
import math
import platform
import time
from pathlib import Path
import jsbsim

PROPERTIES = ["position/h-agl-ft", "attitude/phi-rad", "attitude/theta-rad",
              "velocities/u-fps", "velocities/v-fps", "velocities/w-fps"]

def run(seconds):
    f = jsbsim.FGFDMExec(None)
    f.set_debug_level(0)
    root = Path(f.get_root_dir())
    if not f.load_script(str(root / "scripts/ah1s_flight_test.xml")):
        raise RuntimeError("Could not load upstream helicopter script")
    f.disable_output()
    if not f.run_ic():
        raise RuntimeError("Initialization failed")
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
            assets[str(asset.relative_to(root))] = hashlib.sha256(asset.read_bytes()).hexdigest()
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
    report = {"status": "feasibility_only", "backend": "JSBSim",
              "version": jsbsim.__version__, "python": platform.python_version(),
              "platform": platform.platform(), "script": "ah1s_flight_test.xml",
              "script_variant": 1, "simulated_seconds": rows[-1][0],
              "steps": len(rows), "wall_seconds": elapsed,
              "exact_fresh_instance_replay": rows == replay,
              "properties": ["simulation/sim-time-sec"] + PROPERTIES,
              "final_state": rows[-1], "asset_sha256": assets,
              "trajectory_sha256": hashlib.sha256(json.dumps(rows).encode()).hexdigest(),
              "limitations": "Upstream scripted flight; not fixed-position hover validation. No fault injection or scientific controller-failure outcome."}
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(report, indent=2) + "\n")
    trajectory = a.output.with_suffix(".trajectory.json")
    trajectory.write_text(json.dumps(rows) + "\n")
    print(json.dumps({k:v for k,v in report.items() if k != "asset_sha256"}, indent=2))
    if rows != replay:
        raise SystemExit("Replay differs")

if __name__ == "__main__":
    main()
