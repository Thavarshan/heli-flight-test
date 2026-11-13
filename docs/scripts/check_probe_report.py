"""Verify a JSBSim smoke report against its raw trajectory and hash."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "code"))
from heli_lib.hover_metrics import screen_hover_window


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--report", required=True, type=Path)
    args = p.parse_args()
    report = json.loads(args.report.read_text())
    raw_path = args.report.with_suffix(".trajectory.json")
    rows = json.loads(raw_path.read_text())
    digest = hashlib.sha256(json.dumps(rows).encode()).hexdigest()
    if digest != report["trajectory_sha256"]:
        raise SystemExit("Trajectory SHA-256 mismatch")
    if report["status"] != "feasibility_only":
        raise SystemExit("Unexpected scientific status")
    if not report["exact_fresh_instance_replay"]:
        raise SystemExit("Fresh-instance replay not identical")
    if not rows or len(rows) != report["steps"] or rows[-1] != report["final_state"]:
        raise SystemExit("Trajectory metadata mismatch")
    observed = screen_hover_window(report["properties"], rows)
    if observed != report["hover_screen"]:
        raise SystemExit("Hover screening did not reproduce")
    print("Verified trajectory hash, replay flag and stationarity screen:",
          observed["status"], "(NOT scientific hover validation)")


if __name__ == "__main__":
    main()
