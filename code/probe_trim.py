"""Fail-closed JSBSim built-in trim feasibility on the AH-1S model.

The generic JSBSim tLongitudinal/tFull trimmer is not guaranteed to work
on a helicopter. Independent worker processes with timeouts prevent hangs.
Any "success" is only a solver outcome until a full stationary trace passes.
This exploratory diagnostic does not validate a physical helicopter.
"""
import argparse
import hashlib
import json
import math
import os
import platform
import subprocess
import sys
import tempfile
from pathlib import Path

from heli_lib.control_clock import SimulationClock

DT = .0075
OBS = .15
HORIZON = 25.0
WORKER_TIMEOUT_S = 16
MODE_NAMES = {0: "longitudinal", 1: "full"}
# zero and low forward speeds are separate *hypotheses*, not claimed hover.
CASES = [(mode, speed) for mode in (1, 0) for speed in (0., 2., 5.)]
ASSETS = ("aircraft/ah1s/ah1s.xml",
          "aircraft/ah1s/reset00.xml",
          "aircraft/ah1s/Systems/rotor_control.xml",
          "aircraft/ah1s/Systems/steady_flight_data.xml",
          "systems/afcs.xml")


def _save(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=path.parent, mode="w", encoding="utf-8",
            prefix=path.name+".", suffix=".tmp", delete=False,
        ) as file:
            temp = Path(file.name)
            json.dump(obj, file, indent=2, sort_keys=True, allow_nan=False)
            file.write("\n")
            file.flush()
            os.fsync(file.fileno())
        os.replace(temp, path)
    finally:
        if temp is not None:
            temp.unlink(missing_ok=True)


def _state(f) -> dict:
    props = {
        "time_s": "simulation/sim-time-sec",
        "north_m": "position/distance-from-start-lat-mt",
        "east_m": "position/distance-from-start-lon-mt",
        "agl_ft": "position/h-agl-ft",
        "phi_rad": "attitude/phi-rad",
        "theta_rad": "attitude/theta-rad",
        "u_fps": "velocities/u-fps",
        "v_fps": "velocities/v-fps",
        "w_fps": "velocities/w-fps",
        "rotor_rpm": "propulsion/engine/rotor-rpm",
    }
    state = {key: float(f[name]) for key, name in props.items()}
    if not all(math.isfinite(v) for v in state.values()):
        raise RuntimeError("nonfinite simulator telemetry")
    return state


def worker(mode: int, speed: float, output: Path) -> None:
    import jsbsim
    from heli_lib.hover_metrics import screen_hover_window

    result = {
        "mode": MODE_NAMES[mode],
        "mode_number": mode,
        "initial_calibrated_air_speed_kts": speed,
        "status": "UNRESOLVED",
        "solver_returned": False,
        "backend": "JSBSim",
        "version": jsbsim.__version__,
        "python": platform.python_version(),
    }
    try:
        f = jsbsim.FGFDMExec(None)
        f.set_debug_level(0)
        root = Path(f.get_root_dir())
        result["asset_sha256"] = {
            name: hashlib.sha256((root / name).read_bytes()).hexdigest()
            for name in ASSETS
        }
        if not f.load_model("ah1s"):
            raise RuntimeError("load_model failed")
        if not f.load_ic(str(root/"aircraft/ah1s/reset00.xml"), True):
            raise RuntimeError("load_ic failed")
        f.set_dt(DT)
        f.disable_output()
        f["ic/h-agl-ft"] = 75.
        f["ic/vc-kts"] = speed
        f["ic/roc-fpm"] = 0.
        if not f.run_ic():
            raise RuntimeError("run_ic failed")
        result["before_trim"] = _state(f)
        # JSBSim FGFDMExec official DoTrim modes: 0=longitudinal, 1=full.
        # Direct trim, not simulation/do_simple_trim, with exceptions captured.
        f["simulation/do_trim"] = mode
        result["solver_returned"] = True
        result["after_trim"] = _state(f)
        clock = SimulationClock(DT, OBS, OBS)
        samples = []
        props = (
            "simulation/sim-time-sec", "position/h-agl-ft",
            "position/distance-from-start-lat-mt",
            "position/distance-from-start-lon-mt",
            "attitude/phi-rad", "attitude/theta-rad",
            "velocities/u-fps", "velocities/v-fps", "velocities/w-fps",
            "propulsion/engine/rotor-rpm",
        )
        for step in range(clock.ticks_for_duration(HORIZON)+1):
            if clock.is_observation_tick(step):
                s = _state(f)
                samples.append([s[k] for k in (
                    "time_s","agl_ft","north_m","east_m","phi_rad",
                    "theta_rad","u_fps","v_fps","w_fps","rotor_rpm"
                )])
            if step < clock.ticks_for_duration(HORIZON) and not f.run():
                raise RuntimeError("simulator stopped before horizon")
        # Not a general JSBSim aircraft validation; only an existing candidate
        # screening policy after trim solver returned without an exception.
        result["hover_screen"] = screen_hover_window(
            props, samples, window_s=20., max_sample_gap_s=OBS*1.01)
        result["status"] = (
            "SOLVER_RETURNED_AND_SCREEN_PASS_UNVALIDATED"
            if result["hover_screen"]["status"] == "PASS_CANDIDATE"
            else "SOLVER_RETURNED_BUT_HOVER_NOT_ESTABLISHED"
        )
        result["trace"] = samples
    except Exception as e:
        result["status"] = "TRIM_FAILED_OR_UNRESOLVED"
        result["error_type"] = type(e).__name__
        result["error"] = str(e)
    _save(output, result)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--mode", type=int, choices=(0,1))
    parser.add_argument("--speed", type=float)
    args = parser.parse_args()
    if args.worker:
        if args.mode is None or args.speed is None:
            parser.error("worker needs mode and speed")
        worker(args.mode, args.speed, args.output)
        return

    cases = []
    with tempfile.TemporaryDirectory(prefix="ah1s-trim-") as folder:
        for mode, speed in CASES:
            tmp = Path(folder) / f"mode-{mode}-speed-{speed}.json"
            command = [sys.executable, str(Path(__file__).resolve()),
                       "--worker", "--mode", str(mode), "--speed", str(speed),
                       "--output", str(tmp)]
            try:
                execution = subprocess.run(command, capture_output=True,
                                           text=True, timeout=WORKER_TIMEOUT_S)
                if tmp.is_file():
                    entry = json.loads(tmp.read_text(encoding="utf-8"))
                    entry["worker_exit_code"] = execution.returncode
                else:
                    entry = {
                        "mode": MODE_NAMES[mode], "initial_calibrated_air_speed_kts": speed,
                        "status": "UNRESOLVED_WORKER_EXIT",
                        "worker_exit_code": execution.returncode,
                        "stderr_tail": execution.stderr[-1500:],
                    }
            except subprocess.TimeoutExpired:
                entry = {"mode": MODE_NAMES[mode],
                         "initial_calibrated_air_speed_kts": speed,
                         "status": "UNRESOLVED_WORKER_TIMEOUT",
                         "worker_timeout_seconds": WORKER_TIMEOUT_S}
            cases.append(entry)

    report = {"status": "EXPLORATORY_TRIM_FEASIBILITY",
              "backend": "JSBSim", "initial_agl_ft": 75.,
              "integration_dt_s": DT, "sample_period_s": OBS,
              "simulation_horizon_s": HORIZON,
              "cases": cases,
              "limitations": (
                  "Neither a solver return nor a stationarity pass establishes "
                  "helicopter physical fidelity, a valid trim solution, or a "
                  "certified autopilot. Failed and timed-out attempts are "
                  "reported separately from controller failures."
              )}
    _save(args.output, report)
    print(json.dumps({
        "status": report["status"],
        "cases": [{"mode": x["mode"], "initial_kts":
                   x["initial_calibrated_air_speed_kts"],
                   "status": x["status"],
                   "screen": x.get("hover_screen", {}).get("status"),
                   "reason": x.get("error", x.get("stderr_tail"))}
                  for x in cases],
        "report": str(args.output)
    }, indent=2))
    # Exit zero when diagnostic executes and records all outcomes, even
    # negative solver results. Worker errors remain explicit in evidence.
    if any(x["status"].startswith("UNRESOLVED_WORKER") for x in cases):
        raise SystemExit("One or more trim workers unresolved; see report")


if __name__ == "__main__":
    main()
