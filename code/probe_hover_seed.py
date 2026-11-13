"""Bounded, script-free AH-1S steady-flight-table-informed hover seed screen.

The upstream steady-flight data is unvalidated by this project. This tiny
development sweep is an initialization feasibility diagnostic, NOT a
statistical experiment or validated closed-loop hover-controller tuning.
"""
import argparse
import hashlib
import json
import math
import os
import tempfile
from pathlib import Path

import jsbsim

from probe_scriptfree import READ, MODEL_ASSETS, DT0, SAMPLE_PERIOD, START_AGL_FT
from heli_lib.hover_controller import FT_TO_M

# Selected after inspecting upstream aircraft/ah1s/Systems/steady_flight_data.xml
# (0 knots, 2000-5000 ft ASL near model's KEDW field elevation).
# These are source-model estimates, NOT experimentally established trim.
PHI_TRIM_RAD = -0.049254
THETA_TRIM_RAD = -0.006428
COLLECTIVES = (.57, .615, .66, .71)
LONGITUDINALS = (-.18, -.1558)
LATERALS = (.19, .22)
PEDAL = .39
DURATION_S = 9.0


def trial(collective: float, longitudinal: float, lateral: float) -> dict:
    f = jsbsim.FGFDMExec(None)
    f.set_debug_level(0)
    root = Path(f.get_root_dir())
    if not f.load_model("ah1s"):
        raise RuntimeError("cannot load aircraft without script")
    if not f.load_ic(str(root / "aircraft/ah1s/reset00.xml"), True):
        raise RuntimeError("cannot load aircraft initial conditions")
    f.set_dt(DT0)
    f["ic/h-agl-ft"] = START_AGL_FT
    f["ic/phi-deg"] = math.degrees(PHI_TRIM_RAD)
    f["ic/theta-deg"] = math.degrees(THETA_TRIM_RAD)
    f.disable_output()
    if not f.run_ic():
        raise RuntimeError("run_ic failed")
    settings = {
        "fcs/collective-cmd-norm": collective,
        "fcs/elevator-cmd-norm": longitudinal,
        "fcs/aileron-cmd-norm": lateral,
        "fcs/rudder-cmd-norm": PEDAL,
        "fcs/rpm-governor-active-norm": 1,
        "fcs/adj/collective-profile": 0,
        "fcs/adj/center-sensitivity": 1,
        "ap/afcs/manual/phi-trim-rad": PHI_TRIM_RAD,
        "ap/afcs/manual/theta-trim-rad": THETA_TRIM_RAD,
        "ap/afcs/psi-trim-rad": math.pi,
        "ap/afcs/roll-channel-active-norm": 1,
        "ap/afcs/pitch-channel-active-norm": 1,
        "ap/afcs/yaw-channel-active-norm": 1,
        "ap/afcs/altitude-channel-active-norm": 0,
    }
    for key in settings:
        if key not in f.query_property_catalog(key):
            raise RuntimeError("missing model configuration property "+key)

    ticks = round(SAMPLE_PERIOD / DT0)
    rows = []
    for observation in range(round(DURATION_S / SAMPLE_PERIOD)+1):
        if observation:
            for _ in range(ticks):
                for name, val in settings.items():
                    f[name] = val
                if not f.run():
                    raise RuntimeError("AH-1S backend stopped")
        if abs(f.get_sim_time() - observation*SAMPLE_PERIOD) > 1e-6:
            raise RuntimeError("physical-time observation mismatch")
        row = {"time_s": observation*SAMPLE_PERIOD}
        for name, (prop, factor) in READ.items():
            val = float(f[prop]) * factor
            if not math.isfinite(val):
                raise RuntimeError("nonfinite property "+prop)
            row[name] = val
        rows.append(row)
    start, end = rows[0], rows[-1]
    excursion = math.hypot(end["north_m"]-start["north_m"],
                           end["east_m"]-start["east_m"])
    final_speed = math.sqrt(sum(end[key]**2 for key in ("u_mps","v_mps","w_mps")))
    min_agl = min(v["agl_m"] for v in rows)
    altitude_delta = end["agl_m"] - start["agl_m"]
    # This ranking is only for initial development exploration.
    score = excursion + 2.0*abs(altitude_delta) + 0.5*final_speed
    return {
        "config": {"collective": collective, "longitudinal": longitudinal,
                   "lateral": lateral, "pedal": PEDAL},
        "status": "DEVELOPMENT_ONLY",
        "final_excursion_m": excursion,
        "final_altitude_change_m": altitude_delta,
        "min_agl_m": min_agl,
        "final_body_speed_mps": final_speed,
        "developer_score": score,
        "trace": rows,
        "asset_sha256": {k:hashlib.sha256((root/k).read_bytes()).hexdigest()
                          for k in MODEL_ASSETS},
    }


def _atomic(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    name = None
    try:
        with tempfile.NamedTemporaryFile("w", dir=path.parent, encoding="utf-8",
                                         prefix=path.name+".", suffix=".tmp",
                                         delete=False) as f:
            name = Path(f.name)
            json.dump(value, f, indent=2, sort_keys=True)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(name, path)
    finally:
        if name:
            name.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    cases = []
    for collective in COLLECTIVES:
        for longitudinal in LONGITUDINALS:
            for lateral in LATERALS:
                try:
                    cases.append(trial(collective, longitudinal, lateral))
                except Exception as e:
                    cases.append({
                        "status": "UNRESOLVED",
                        "config": {"collective": collective,
                                   "longitudinal": longitudinal, "lateral": lateral},
                        "reason": type(e).__name__+": "+str(e),
                    })
    available = [x for x in cases if x["status"]=="DEVELOPMENT_ONLY"]
    viable = [x for x in available if x["min_agl_m"]>=5.0]
    best = min(viable, key=lambda x: x["developer_score"]) if viable else None
    report = {
        "status": "NO_AIRBORNE_SEED" if not viable else "POSSIBLE_SEED_NOT_TRIMMED",
        "backend": "JSBSim", "backend_version": jsbsim.__version__,
        "case_count": len(cases), "valid_backend_case_count": len(available),
        "airborne_development_case_count": len(viable),
        "sfd_initial_angles_rad": {"phi": PHI_TRIM_RAD,"theta":THETA_TRIM_RAD},
        "source": "JSBSim-Team/jsbsim aircraft/ah1s/Systems/steady_flight_data.xml",
        "initial_airborne_altitude_m": START_AGL_FT*FT_TO_M,
        "duration_s": DURATION_S,
        "candidate": best["config"] if best else None,
        "cases": cases,
        "limitations": (
            "This is an untrimmed artificial start with source-model table angles "
            "and perfect commanded state. Ranking is a heuristic dev-only screen, "
            "not validation, global optimization, a hover controller or evidence "
            "that any initial state is stable or physical."
        ),
    }
    _atomic(args.output, report)
    print(json.dumps({
        "status": report["status"], "case_count": len(cases),
        "airborne_case_count": len(viable),
        "candidate": report["candidate"],
        "candidate_metrics": {
            k: best[k] for k in ("final_excursion_m",
                                 "final_altitude_change_m",
                                 "min_agl_m","final_body_speed_mps")
        } if best else None,
        "limitations": report["limitations"],
    }, indent=2))
    if not available:
        raise SystemExit("All 16 script-free cases were backend failures")


if __name__ == "__main__":
    main()
