# JSBSim native trim → ArduPilot helicopter SITL: bounded development gates

**Date:** 2026-11-14, based on 2026-11-13 UTC CI run logs. **Status:** exploratory backend transition; no validated 20-second hover, no confirmatory software-reduction evidence.

## 1. JSBSim AH-1S: stop after one bounded native-trim attempt

Run: [CI #43528782116](https://github.com/Thavarshan/heli-flight-test/actions/runs/43528782116), using `code/probe_native_trim.py`, JSBSim 1.2.3 and direct aircraft/IC loading without stock flight script.

The native `simulation/do_simple_trim` callback was invoked in each of these independent cases:

| Seed configuration | Full trim | Longitudinal trim |
| --- | --- | --- |
| Manual pilot commands + roll/pitch/yaw AFCS | `TrimFailureError: Trim Failed` | `TrimFailureError: Trim Failed` |
| Source SFD tables + AFCS | `TrimFailureError: Trim Failed` | `TrimFailureError: Trim Failed` |
| Manual commands, AFCS disabled | `TrimFailureError: Trim Failed` | `TrimFailureError: Trim Failed` |

All **six** were rejected; hence no trimmed state exists from this experiment to screen for 45 seconds. `NO_STABLE_HOVER_IN_BOUNDED_NATIVE_TRIM_TRIALS` is accurate. This does **not** prove JSBSim is incapable of helicopter hover, or that any real controller failed. No further AH-1S tuning is authorized in this bounded decision before independent model expertise.

## 2. First ArduPilot SITL integration and firmware mismatch

ArduPilot conventional-heli source: [SIM_Helicopter.cpp](https://github.com/ArduPilot/ardupilot/blob/fb773567896014da007bca58358704d4a0d8516f/libraries/SITL/SIM_Helicopter.cpp). Its default conventional model is a roughly **4.54 kg** helicopter, **not** the JSBSim AH-1S. ArduPilot's Copter source explicitly defines a **separate** target `arducopter-heli` with `FRAME_CONFIG=HELI_FRAME` in [ArduCopter/wscript](https://github.com/ArduPilot/ardupilot/blob/fb773567896014da007bca58358704d4a0d8516f/ArduCopter/wscript). The official [SITL frame metadata](https://github.com/ArduPilot/ardupilot/blob/fb773567896014da007bca58358704d4a0d8516f/Tools/autotest/pysim/vehicleinfo.py) names `bin/arducopter-heli` for `-f heli`.

Initial prebuilt generic SITL executable (wrong vehicle firmware, preserved for comparison): pinned **ArduCopter V4.7.2**, source commit `fb773567896014da007bca58358704d4a0d8516f`; binary SHA-256 `caed35e4cb796ec06cac40b09566a18251771486b1cbac5e2bf16b7a5ed5045d`. Default heli param file downloaded from the upstream repo: SHA-256 `5477a1727344d56bf68675330d52ac7e6aca8a9b0df49e714794678be78975f6`. Evidence is [CI #43529203470](https://github.com/Thavarshan/heli-flight-test/actions/runs/43529203470), following a fixed MAVLink subscription and zero-position rejection. It confirmed `FRAME_CLASS=6`, actual heartbeat/attitude, and valid home-relative GPS position after 30 uninitialized zero-position samples.

The subsequent real GUIDED-mode test on that **generic** executable [CI #43529370167](https://github.com/Thavarshan/heli-flight-test/actions/runs/43529370167) had a valid GPS fix (type 6), navigation, GUIDED mode, **but did not arm or take off**. MAVLink arming command 400 returned `MAV_RESULT_FAILED`; autopilot reported `PreArm: Motors: Check frame class and type`. This is consistent with loading the generic multicopter firmware with heli frame class. The correct remedy is to build `arducopter-heli`, **not to disable arming checks or change frame class to a multicopter**.

ArduPilot docs additionally require helicopter rotor motor-interlock off (RC8 low) for arming, then on **after** successful arming for rotor run-up. We corrected the testing sequence accordingly. See [official helicopter motor/interlock instructions](https://ardupilot.org/copter/docs/traditional-helicopter-connecting-apm.html).

## 3. Helicopter-specific binary trial

A separate GitHub Actions job `ardupilot-compiled-heli-flight` checks out ArduPilot commit `fb773567896014da007bca58358704d4a0d8516f` with submodules, compiles the explicit `bin/arducopter-heli` target, verifies source target `FRAME_CONFIG=HELI_FRAME`, then runs:
1. Headless autonomous helicopter MAVLink heartbeat, telemetry and valid home position.
2. Simulated-only GUIDED-mode / safe motor-interlock / arm / rotor run-up / 8 m takeoff / 20 s sampled-position-hover diagnostic.
3. Full log and artifact capture, including negative outcomes, firmware and compiled binary hashes.

**The native-heli build/flight trial must pass before selecting this backend.** The eventual `PASS_CANDIDATE_NOT_VALIDATED`, if observed, would only be a pre-validation hover-screen candidate, not real-aircraft model fidelity, cross-machine deterministic replay or a publication finding. Scientific gate #2/#3 remains open until a stable nominal hover is independently demonstrated and controller/physics clocks are appropriately separated.

## 4. Reproducibility and research safety
- Exact upstream source commit is pinned; no bundled upstream GPL source/model is redistributed by this repository.
- All downloads and source builds use public GitHub Actions runners; experiments are loopback-only with no real vehicle connection.
- Upstream heli source and AH-1S model have different aircraft masses, control assumptions and physical validation limits. Never pool their trajectories.
- Current MAVLink samples and wall-clock command timing are not lockstep simulator replay.
- Do not conduct gust/delay experiments or confirmatory replay reduction on this incomplete baseline.
