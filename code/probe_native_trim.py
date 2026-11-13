"""One bounded JSBSim native hover-trim feasibility gate (development only).

Uses the official simulation/do_simple_trim callback, never a stock flight
script. Native FGTrim convergence by itself is NOT a validated helicopter hover.
Preserves negative outcomes and only screens timed flight after trim success.
"""
import argparse
import hashlib
import json
import math
import os
import tempfile
from pathlib import Path
import jsbsim

from heli_lib.hover_metrics import screen_hover_window
from probe_scriptfree import MODEL_ASSETS, READ, DT0
from probe_seed_extended import _hover

PERIOD_S = 0.15
DURATION_S = 45.0
TRIM_MODES = {"full": 1, "longitudinal": 0}
CASES = {
    "manual_afcs": {
        "fcs/collective-cmd-norm": 0.615,
        "fcs/elevator-cmd-norm": -0.1558,
        "fcs/aileron-cmd-norm": 0.19095,
        "fcs/rudder-cmd-norm": 0.39,
        "ap/afcs/roll-channel-active-norm": 1.0,
        "ap/afcs/pitch-channel-active-norm": 1.0,
        "ap/afcs/yaw-channel-active-norm": 1.0,
        "ap/afcs/manual/phi-trim-rad": -0.049254,
        "ap/afcs/manual/theta-trim-rad": -0.006428,
        "fcs/automatic/steady-flight-data-enable": 0.0,
    },
    "sfd_afcs": {
        "fcs/collective-cmd-norm": 0.0,
        "fcs/elevator-cmd-norm": 0.0,
        "fcs/aileron-cmd-norm": 0.0,
        "fcs/rudder-cmd-norm": 0.0,
        "ap/afcs/roll-channel-active-norm": 1.0,
        "ap/afcs/pitch-channel-active-norm": 1.0,
        "ap/afcs/yaw-channel-active-norm": 1.0,
        "fcs/automatic/steady-flight-data-enable": 1.0,
    },
    "manual_no_afcs": {
        "fcs/collective-cmd-norm": 0.615,
        "fcs/elevator-cmd-norm": -0.1558,
        "fcs/aileron-cmd-norm": 0.19095,
        "fcs/rudder-cmd-norm": 0.39,
        "ap/afcs/roll-channel-active-norm": 0.0,
        "ap/afcs/pitch-channel-active-norm": 0.0,
        "ap/afcs/yaw-channel-active-norm": 0.0,
        "fcs/automatic/steady-flight-data-enable": 0.0,
    },
}
PILOT_KEYS = (
    "fcs/collective-cmd-norm", "fcs/elevator-cmd-norm",
    "fcs/aileron-cmd-norm", "fcs/rudder-cmd-norm",
)


def steps_per_tick(dt_s):
    if not (math.isfinite(dt_s) and dt_s > 0):
        raise ValueError("positive finite timestep required")
    n = round(PERIOD_S / dt_s)
    if n < 1 or not math.isclose(n * dt_s, PERIOD_S, abs_tol=1e-10):
        raise ValueError("timestep must divide the external pilot tick")
    return n


def attempt(case_name, mode_name, *, factor=1):
    dt = DT0 / factor
    steps = steps_per_tick(dt)
    exec_ = jsbsim.FGFDMExec(None)
    exec_.set_debug_level(0)
    root = Path(exec_.get_root_dir())
    if not exec_.load_model("ah1s"):
        raise RuntimeError("load_model failed")
    if not exec_.load_ic(str(root / "aircraft/ah1s/reset00.xml"), True):
        raise RuntimeError("load_ic failed")
    exec_.set_dt(dt)
    exec_["ic/h-agl-ft"] = 75
    exec_["ic/phi-deg"] = math.degrees(-0.049254)
    exec_["ic/theta-deg"] = math.degrees(-0.006428)
    exec_.disable_output()
    if not exec_.run_ic():
        raise RuntimeError("run_ic failed")
    if abs(exec_.get_delta_t() - dt) > 1e-9:
        raise RuntimeError("integration timestep not accepted")
    setup = {
        "fcs/rpm-governor-active-norm": 1.0,
        "fcs/adj/collective-profile": 0.0,
        "fcs/adj/center-sensitivity": 1.0,
        "ap/afcs/psi-trim-rad": math.pi,
        "ap/afcs/altitude-channel-active-norm": 0.0,
        **CASES[case_name],
    }
    for prop, value in setup.items():
        if prop not in exec_.query_property_catalog(prop):
            raise RuntimeError("missing model setup property " + prop)
        exec_[prop] = value
    if "simulation/do_simple_trim" not in exec_.query_property_catalog("simulation/do_simple_trim"):
        raise RuntimeError("this JSBSim version exposes no documented trim callback")
    hashes = {item: hashlib.sha256((root / item).read_bytes()).hexdigest()
              for item in MODEL_ASSETS}
    initial = {key: float(exec_[prop])*scale for key,(prop,scale) in READ.items()}
    try:
        # Official JSBSim engine, Full (1) and Longitudinal (0) trim modes.
        exec_["simulation/do_simple_trim"] = TRIM_MODES[mode_name]
        completed = bool(exec_["simulation/trim-completed"])
    except Exception as error:
        return {
            "status": "TRIM_REJECTED",
            "mode": mode_name, "case": case_name, "dt_s": dt,
            "exception_type": type(error).__name__,
            "exception": str(error)[:900],
            "model_assets_sha256": hashes, "initial": initial,
        }
    if not completed:
        return {
            "status": "TRIM_NOT_COMPLETED", "case": case_name,
            "mode": mode_name, "dt_s": dt, "model_assets_sha256": hashes,
            "initial": initial,
        }
    # Importantly do NOT overwrite JSBSim's own optimized controls with the
    # seed values after trim: record and hold the resulting commands.
    resulting_commands = {key: float(exec_[key]) for key in PILOT_KEYS}
    trace = []
    for tick in range(round(DURATION_S/PERIOD_S)+1):
        if tick:
            for _ in range(steps):
                for key, value in resulting_commands.items():
                    exec_[key] = value
                if not exec_.run():
                    raise RuntimeError("simulator terminated during post-trim hold")
        t = tick * PERIOD_S
        if abs(exec_.get_sim_time()-t) > 2e-6:
            raise RuntimeError("physical-time pilot clock mismatch")
        row = {"time_s": t}
        for key, (prop, scale) in READ.items():
            value = float(exec_[prop]) * scale
            if not math.isfinite(value):
                raise RuntimeError("nonfinite post-trim state: " + prop)
            row[key] = value
        trace.append(row)
    return {
        "status": "POST_TRIM_SCREENED", "case": case_name, "mode": mode_name,
        "dt_s": dt, "external_pilot_period_s": PERIOD_S,
        "external_tick_count": round(DURATION_S/PERIOD_S),
        "internal_afcs_remains_timestep_coupled": True,
        "resulting_commands": resulting_commands,
        "model_assets_sha256": hashes, "initial": initial,
        "screen": _hover(trace), "trace": trace,
    }


def _atomic(path, report):
    path.parent.mkdir(parents=True, exist_ok=True)
    name=None
    try:
        with tempfile.NamedTemporaryFile("w",dir=path.parent,encoding="utf-8",
                                         prefix=path.name+".",suffix=".tmp",
                                         delete=False) as stream:
            name=Path(stream.name)
            json.dump(report,stream,sort_keys=True,indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name,path)
    finally:
        if name:
            name.unlink(missing_ok=True)


def decide(records):
    if not records:
        return "UNRESOLVED"
    screened=[r for r in records if r["status"]=="POST_TRIM_SCREENED"]
    if any(r["screen"]["status"]=="PASS_CANDIDATE" for r in screened):
        return "TRIM_CANDIDATE_NOT_VALIDATED"
    if any(r["status"]=="BACKEND_ERROR" for r in records):
        return "UNRESOLVED"
    return "NO_STABLE_HOVER_IN_BOUNDED_NATIVE_TRIM_TRIALS"


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()
    trials=[]
    for case in CASES:
        for mode in TRIM_MODES:
            try:
                trials.append(attempt(case,mode))
            except Exception as error:
                trials.append({"status":"BACKEND_ERROR","case":case,
                               "mode":mode, "exception_type":type(error).__name__,
                               "exception":str(error)[:900]})
    status=decide(trials)
    report={
        "status":status,
        "backend":"JSBSim","version":jsbsim.__version__,
        "physical_control_clock_s":PERIOD_S,
        "dt_s":DT0,
        "seconds_if_trim_succeeds":DURATION_S,
        "cases":trials,
        "limitations":"One bounded development-only native FGTrim feasibility attempt; "
          "trim does not establish hover, published fidelity or numerical "
          "convergence; model AFCS is still physics-clock coupled.",
    }
    _atomic(args.output,report)
    print(json.dumps({
        "status":status,
        "cases": [{key:r.get(key) for key in (
            "case","mode","status","exception_type","exception")}
            | {"hover_screen": r.get("screen",{}).get("status")}
            for r in trials],
        "limitations": report["limitations"],
    },indent=2))
    if status=="UNRESOLVED":
        raise SystemExit("JSBSim probe had unexpected backend errors; inspect artifact")


if __name__=="__main__":
    main()
