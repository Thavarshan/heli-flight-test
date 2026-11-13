# AH-1S control-response and position-feedback development pilot — 2026-11-13

**Status: pre-validation exploratory evidence only. No stable-hover claim.**

## Reproducible sources
- [Control-response CI run #43403687934](https://github.com/Thavarshan/heli-flight-test/actions/runs/43403687934), commit `87507df425f55d380d4a052a6dec91521ad8ce94`.
- [Initial feedback CI run #43403867980](https://github.com/Thavarshan/heli-flight-test/actions/runs/43403867980), commit `98e7aeec73b77b3215144b2d27c476738b87964f`.
- All runs use the installed JSBSim 1.2.3 upstream AH-1S stock flight script, variant 1. Artifacts (JSON with model asset SHA-256 hashes and state samples) are uploaded to their respective CI runs for seven days, and regenerated with the commands in README.
- Independent fresh simulator instances are used for each control perturbation and a separate replay. The starting state was compared for equality. The stock AFCS and flight events are **not disabled**.

## Exploratory pilot input response
Apply +0.06 and -0.06 normalized pilot command relative to the value at 45 s, then observe for 2 s. The selected single-channel primary readout differences versus unchanged flight are:

| Input | Primary readout | -0.06 difference | +0.06 difference | Classification |
| --- | --- | ---: | ---: | --- |
| Collective | AGL, ft | -5.719 | +5.593 | Positive transient response |
| Longitudinal | Body pitch rate, rad/s | +0.006713 | -0.006601 | Negative transient response |
| Lateral | Body roll rate, rad/s | -0.004068 | +0.004088 | Positive transient response |
| Pedal | Body yaw rate, rad/s | -0.011901 | +0.011855 | Positive transient response |

All four actuators showed nonzero paired perturbation response. This is
local sensitivity at one non-trimmed state with controller and script
couplings; it is not proof of globally consistent control signs, an
independent stable trim, or fidelity to measured helicopter dynamics.

## 25-second exploratory position-feedback trial

Starting from a fresh instance of the stock demonstration at t=45 s, set
the reference to that instant's position/altitude and compare no new
feedback to a bounded, heuristic position/velocity control proposal.
Controller step period 0.15 s; JSBSim integration step 0.0075 s. The
stock script and AFCS remain active.

| Outcome (descriptive only) | Unchanged stock script | Development feedback |
| --- | ---: | ---: |
| Final horizontal distance from reference, m | 35.688 | 35.300 |
| Sampled horizontal RMS distance, m | 20.051 | 16.879 |
| Minimum sampled AGL, m | 13.422 | 13.422 (rounded) |

The feedback trajectory exactly replayed in a new instance on this
CI runner; no pilot command overwrites were detected during the
trial. The feedback **did not achieve fixed-position hover**.
A reduction in sample-level RMS error in this *single developmental
trial* is not a scientific effect-size result; there is no multi-seed,
held-out, perturbation or model-convergence validation.

## Scientific gate
Before faults or a paper evaluation: establish controlled steady hover,
independently validate model/control signs and true trim, remove stock
script interference, test h / h/2 / h/4 with fixed controller periods,
freeze thresholds only after development, and collect independent cases.
Negative and failed experiments must remain in evidence.
