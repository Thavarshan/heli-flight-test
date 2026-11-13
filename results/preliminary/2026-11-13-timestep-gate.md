# Numerical sensitivity and script-free AH-1S hover-seed gates — 2026-11-13

**Preliminary developer diagnostics; the scientific model/hover gate has NOT
passed.** These are not independent confirmatory samples, model validation
results, or evidence of real helicopter dynamics.

## Source and reproducibility
- Pinned Python dependency: `jsbsim==1.2.3`.
- [Scripted h/h2/h4 CI](https://github.com/Thavarshan/heli-flight-test/actions/runs/43405525816)
  using `code/probe_timestep.py`.
- [Script-free model/IC load CI](https://github.com/Thavarshan/heli-flight-test/actions/runs/43405625415)
  using `code/probe_scriptfree.py`.
- [16-case source-table seed screen CI](https://github.com/Thavarshan/heli-flight-test/actions/runs/43405781276)
  using `code/probe_hover_seed.py`.
- [45-second independent seed pilot CI](https://github.com/Thavarshan/heli-flight-test/actions/runs/43406014004)
  using `code/probe_seed_extended.py`.
- Raw JSON, full trajectories, relevant model asset SHA-256 hashes and failed
  cases are uploaded as short-lived CI artifacts. Regenerate with runner
  commands documented in README rather than treating CI artifact retention
  as permanent experimental archival.

## 1. Upstream flight-script numerical sensitivity

The original upstream AH-1S variant 1 remains active. Three independent
runs used integration timesteps `0.0075`, `0.00375`, `0.001875` s
and the **same 0.15 s observation clock**, collecting 301 samples over
45 simulated seconds. No flight-controller gain was retuned.

| Compared to h = 0.0075s | Max north difference | Max east difference | Max AGL difference |
| --- | ---: | ---: | ---: |
| h/2 | 14.901 m | 9.154 m | 3.588 m |
| h/4 | 76.246 m | 27.208 m | 15.386 m |

**Interpretation:** there is major trajectory sensitivity to integration
step; it does not become monotonically smaller when the timestep is refined
relative to `h`. This is **not evidence that the simulator numerics are
fundamentally defective**. The stock flight script contains ramp/event
logic and a built-in AFCS evaluated with the integration schedule, so the
*controller update timing was NOT held fixed*. A constant output sample
period is not equivalent to a fixed controller sample period. Consequently
**this experiment is NOT a valid controlled convergence study**. It
demonstrates why a separated controller/event clock is required.

## 2. Direct model initialization without the stock script

The independent model+initial-condition loader succeeded at all three
timesteps. It applies an artificial `75 ft` AGL initial state (not a
trim solution), plus pilot controls and governor directly, for 4.5 s.

| Integration step | Minimum AGL over 4.5s | Peak rotor RPM |
| --- | ---: | ---: |
| h | 1.954 m | 318.922 |
| h/2 | 1.717 m | 321.145 |
| h/4 | 1.766 m | 325.163 |

The aircraft lost most of its artificial initial altitude. No stable
hover claim is possible from this startup.

## 3. SFD-inspired initial-angle/command development seeds

The upstream
[AH-1S steady-flight data XML](https://github.com/JSBSim-Team/jsbsim/blob/master/aircraft/ah1s/Systems/steady_flight_data.xml)
contains *estimated* near-zero airspeed attitude and control tables.
Using `phi=-0.049254 rad`, `theta=-0.006428 rad` as initialization
guesses and the model's AFCS, a **16-case, 9 s** bounded command grid was
run without the stock flight script. Four candidates stayed at least
5 m AGL. The candidate with the lowest *explicit, exploratory* dev score
had normalized pilot command values:
`collective=.71, longitudinal=-.1558, lateral=.22, pedal=.39`.

Its 9s net horizontal displacement was 0.385 m but it lost 4.354 m
of altitude and ended with **4.225 m/s** body velocity. The short
endpoint alone was therefore misleading: **not stable hover**.

The same candidate was independently run for 45s at `h`, `h/2`,
`h/4`. All three final-20s stationarity screens returned
`FAIL_CANDIDATE`. For `h` only the final-20s window showed:
- Peak body speed **5.473 m/s**.
- Horizontal excursion **20.231 m**.
- AGL altitude span **107.151 m**, significantly exceeding the
  exploratory `2m` limit.

The full 45s trajectory reproduced **exactly** from a fresh instance
at `h` in CI after correcting the replay-comparison bookkeeping.
Byte-identical reruns on one platform do not demonstrate step-size
robustness. AFCS update frequency still changes with physics step.

## Decision: current validation gate = BLOCKED
1. Develop a documented helicopter trim process (rather than assuming that
   a short-lived low-displacement trajectory is trimmed).
2. Establish a controller whose measurement/control update ticks remain
   fixed in physical time independently of the physics integrator.
3. Verify engine/governor, rotor actuator mapping, units/frames, force
   response and ground contact using primary aircraft/model sources.
4. Perform `h/h2/h4` comparisons **after** holding controller and
   sensor schedules, input events and initialization identical.
5. Include independent published helicopter behaviour comparison and
   numerical tolerance selection **before** any confirmatory failure
   search, replay-aware reduction or paper results.

No scientific threshold is frozen; the SFD data and this aircraft model
are not independently verified physical flight data.
