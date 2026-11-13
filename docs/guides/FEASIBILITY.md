# Preliminary feasibility — 2026-11-02

## Local experiment
JSBSim 1.2.3 was chosen as a pinned exploratory build, not asserted to be the latest release. Python 3.11.18 on Apple Silicon. Installed using requirements-probe.txt. Upstream AH-1S flight-test script variant 1 ran for 60 simulated seconds (8,000 integration steps) in approximately 0.16 seconds excluding initialization and asset hashing. Two fresh instances produced exactly equal sampled trajectories on this environment. See results/preliminary/jsbsim-probe.json for asset hashes, runtime and final state. Full local trajectories are ignored by git and regenerable.

This checks loading, finite integration and same-environment replay only. The final body velocities were nonzero. The script is a staged flight demonstration, not our fixed-position hover controller. No stable-hover, physical fidelity, cross-platform reproducibility or timestep-convergence claim follows.

Reproduce from repository root:
```sh
uv venv --python 3.11 .venv
uv pip install --python .venv/bin/python -r requirements-probe.txt
.venv/bin/python code/probe_backend.py --seconds 60 --output results/preliminary/jsbsim-probe.json
```

## Backend comparison
| Candidate | Evidence inspected | Advantages for this project | Unresolved work |
| --- | --- | --- | --- |
| JSBSim Python + packaged AH-1S | Installed assets, rotor API, upstream example script | In-process headless execution, property access, inexpensive repeated runs | Aircraft provenance and validation, trim/position hold, fault interface semantics |
| ArduPilot SITL helicopter | Official SITL documentation and SIM_Helicopter.cpp | Real autopilot implementation; helicopter physics source available | Build/runtime not tested here; built-in dynamics need fidelity assessment; process orchestration and sensor-delay semantics |

Provisional decision: investigate JSBSim first because the local feasibility probe works. Do not freeze the scientific backend until hover and validation gates pass. ArduPilot remains an alternative/controller integration candidate, not a claimed tested dependency.

Licensing: JSBSim repository COPYING contains LGPL 2.1; ArduPilot helicopter source header states GPL v3 or later. Independently inspect all selected aircraft/model assets and dependencies before redistribution. No third-party model source is copied into this repository. The new project's own license remains undecided.

Sources inspected:
- https://jsbsim-team.github.io/jsbsim/classJSBSim_1_1FGRotor.html
- https://raw.githubusercontent.com/JSBSim-Team/jsbsim/master/COPYING
- https://raw.githubusercontent.com/ArduPilot/ardupilot/master/libraries/SITL/SIM_Helicopter.cpp
- https://ardupilot.ardupilot.org/dev/docs/sitl-simulator-software-in-the-loop.html

## Next experiment
Inspect AH-1S controller and trim properties; establish a documented hover initialization and fixed-position reference. Log position, attitude, body velocity, rotor speed and controls. Check control signs and timestep sensitivity. Use a trusted reference to assess model behaviour before testing novel search.

## 2026-11-13 reproducibility extension

The upstream [AH-1S flight test script](https://github.com/JSBSim-Team/jsbsim/blob/master/scripts/ah1s_flight_test.xml)
describes variant **1** as maximum speed flight and includes a temporary
approximately 75 ft AGL hover-like phase before flying off. It is **not**
an autonomous fixed-position hold experiment. The probe keeps variant 1
and now records displacement-from-start north/east (metres), body
velocity (ft/s), AGL (ft), roll/pitch (radians), and rotor RPM.
[JSBSim documentation](https://jsbsim-team.github.io/jsbsim/classJSBSim_1_1FGFDMExec.html)
distinguishes loading an aircraft and initializing a simulation from
validating its flight behaviour; even kinematically consistent initial
conditions are not automatically trim.

The last 20 seconds are screened using **development-only** limits:
peak body speed <= 1.0 m/s, maximum displacement from the window start
<= 3.0 m, altitude span <= 2.0 m, maximum absolute roll/pitch <= 10
degrees, minimum AGL >= 5 m, rotor speed >= 1 RPM. These numbers are
engineering screening choices, **not** aviation standards or frozen
scientific failure thresholds. A missing property, nonfinite state,
duplicate timestamp, incomplete window or sampling gap > 1 s yields
`UNRESOLVED`, not a favorable result. `PASS_CANDIDATE` never means
"validated hover." No physical-aircraft fidelity or control stability
claim follows from any result of this script.

Reproduce the screen after installing `requirements-probe.txt`:

```sh
python -m unittest discover -s tests -v
python code/probe_backend.py --seconds 45 --output smoke-output/jsbsim-probe.json
python docs/scripts/check_probe_report.py --report smoke-output/jsbsim-probe.json
```

The checker verifies the full trajectory SHA-256, stored endpoints, replay
flag and freshly computed screen; CI retains the run as a short-lived
artifact. Saved `results/preliminary/jsbsim-probe.json` predates this
extension; never interpret missing new fields as scientific findings.
