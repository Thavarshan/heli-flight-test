"""Do not claim hover without a full final-window stationarity screen.

Take a single 9s source-table development seed for a longer, independent,
script-free hover feasibility study at h, h/2 and h/4. No confirmatory study.
"""
import argparse
import json
import os
import tempfile
from pathlib import Path

from probe_hover_seed import trial, DT0, SAMPLE_PERIOD, PHI_TRIM_RAD, THETA_TRIM_RAD
from heli_lib.numerical_validation import compare_traces
from heli_lib.hover_metrics import screen_hover_window

CONTROL = {"collective": .71, "longitudinal": -.1558,
           "lateral": .22, "pedal": .39}
DURATION_S = 45.0


def _hover(trace):
    properties = [
        "simulation/sim-time-sec",
        "position/h-agl-ft",
        "position/distance-from-start-lat-mt",
        "position/distance-from-start-lon-mt",
        "attitude/phi-rad",
        "attitude/theta-rad",
        "velocities/u-fps",
        "velocities/v-fps",
        "velocities/w-fps",
        "propulsion/engine/rotor-rpm",
    ]
    rows = [[r["time_s"],r["agl_m"]/0.3048,r["north_m"],r["east_m"],
             r["phi_rad"],r["theta_rad"],r["u_mps"]/0.3048,
             r["v_mps"]/0.3048,r["w_mps"]/0.3048,r["rotor_rpm"]]
            for r in trace]
    return screen_hover_window(properties,rows,window_s=20,
                               max_sample_gap_s=SAMPLE_PERIOD*1.01)


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
        if name is not None:
            name.unlink(missing_ok=True)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",required=True,type=Path)
    args=ap.parse_args()
    cases = {}
    failures=[]
    for factor in (1,2,4):
        try:
            result=trial(CONTROL["collective"],CONTROL["longitudinal"],
                         CONTROL["lateral"],duration_s=DURATION_S,
                         dt_s=DT0/factor)
            cases[str(factor)]={"status":"OK", **result,
                                "hover_screen":_hover(result["trace"]),
                                "dt_s":DT0/factor}
        except Exception as exc:
            failures.append(factor)
            cases[str(factor)]={"status":"UNRESOLVED","reason":
                                type(exc).__name__+": "+str(exc)}
    replay=False
    comparisons={}
    if not failures:
        try:
            other=trial(CONTROL["collective"],CONTROL["longitudinal"],
                        CONTROL["lateral"],duration_s=DURATION_S,dt_s=DT0)
            replay=other=={k:v for k,v in cases["1"].items()
                           if k not in ("status","hover_screen","dt_s")}
            for factor in ("2","4"):
                if cases["1"]["asset_sha256"] != cases[factor]["asset_sha256"]:
                    comparisons[factor]={"status":"UNRESOLVED","reason":"asset_change"}
                    failures.append(int(factor))
                else:
                    comparisons[factor]=compare_traces(
                        cases["1"]["trace"],cases[factor]["trace"],
                        expected_period_s=SAMPLE_PERIOD)
        except Exception as exc:
            failures.append(1)
            comparisons["replay"]={"status":"UNRESOLVED",
                                   "reason":type(exc).__name__+": "+str(exc)}
    report={
        "status":"UNRESOLVED" if failures or not replay else "LONG_HOVER_SEED_DIAGNOSTIC",
        "source":"Previously recorded 9s SFD-inspired development grid",
        "candidate":CONTROL,
        "initial_table_trim_phi_rad":PHI_TRIM_RAD,
        "initial_table_trim_theta_rad":THETA_TRIM_RAD,
        "duration_s":DURATION_S,
        "sample_period_s":SAMPLE_PERIOD,
        "fresh_instance_exact_replay":replay,
        "cases":cases,
        "comparison_to_h":comparisons,
        "limitations":"Artificial untrimmed initialization with AFCS, no external "
          "model validation, no independently verified control authority "
          "or fixed controller rate under timestep changes. "
          "Candidate hover status is exploratory, not safety evidence."
    }
    _atomic(args.output,report)
    print(json.dumps({
        "status":report["status"],
        "exact_fresh_instance_replay":replay,
        "hover_screens":{k:v.get("hover_screen",{"status":v["status"]})
                         for k,v in cases.items()},
        "comparison_max_north_error_m":{
            k:v.get("max_abs_difference",{}).get("north_m")
            for k,v in comparisons.items()
        },
        "limitations":report["limitations"],
    },indent=2))
    if report["status"]=="UNRESOLVED":
        raise SystemExit("Long candidate evaluation unresolved; see report")


if __name__=="__main__":
    main()
