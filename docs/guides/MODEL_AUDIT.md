# AH-1S research-model provenance audit — 2026-11-13

## Source identity and intellectual-property constraints

The exploratory baseline uses the AH-1S / Bell 209 model distributed with
the pinned JSBSim Python wheel (`jsbsim==1.2.3`) and stock script variant 1.
Model-specific and system assets are supplied by the dependency; this
repository does not copy the model source.

The upstream
[AH-1S aircraft definition](https://github.com/JSBSim-Team/jsbsim/blob/master/aircraft/ah1s/ah1s.xml)
identifies **Thomas Kreitler** as author and describes the configuration as
`release="ALPHA"`. Its file header declares a **GPL** license and offers
an alternative **CC-BY-NC-SA** permission for certain published open-source
uses. This is *model-specific*; it must not be confused with the separate
LGPL license of JSBSim's engine code. The aircraft header expressly states
that the model uses public materials and guesses, and that validation was
limited to qualitative flyability and possibly published performance.
The header does *not* establish certification, quantitative hover fidelity,
or an aircraft-flight-data validation record.

**Redistribution decision:** keep this project as tooling that references
installed upstream assets; do not vendor the GPL/alternative-licensed model
or package it into another deliverable until its exact license terms and
distribution obligations have been reviewed. Retain source notices and
model attribution in any later redistribution. The repo's own license
remains undecided, so no blanket license claim is made here.

## Model and controller interfaces inspected

- [AH-1S reset00.xml](https://github.com/JSBSim-Team/jsbsim/blob/master/aircraft/ah1s/reset00.xml):
  initial condition at 6.3 ft AGL, zero body velocity, heading 180 degrees.
  These are kinematic initial conditions, **not** a helicopter trim solution.
- [AH-1S flight script](https://github.com/JSBSim-Team/jsbsim/blob/master/scripts/ah1s_flight_test.xml):
  variant 1 is a maximum-speed flight test. It includes a scripted approximate
  75-ft AGL hover phase, later fly-off events and activated AFCS; it is
  **not** a closed-loop station-keeping controller or autonomous position hold.
- [Rotor control XML](https://github.com/JSBSim-Team/jsbsim/blob/master/aircraft/ah1s/Systems/rotor_control.xml):
  pilot inputs `fcs/collective-cmd-norm`, `fcs/elevator-cmd-norm`,
  `fcs/aileron-cmd-norm`, `fcs/rudder-cmd-norm`, with nonlinear
  mappings, mixing and lags before rotor actuator outputs. Sign inference
  from a direct property assignment alone would be unsound.
- [AFCS XML](https://github.com/JSBSim-Team/jsbsim/blob/master/systems/afcs.xml):
  roll, pitch, yaw and optional altitude stabilization channels are available.
  This is an *attitude/heading/altitude* system, not a position controller.
- [JSBSim initial-condition API](https://jsbsim-team.github.io/jsbsim/python/FGInitialCondition.html):
  initial conditions can be kinematically consistent without being
  dynamically trimmed. `run_ic()` must not be called a trim operation.

All links above refer to publicly inspected **upstream HEAD**, not a guarantee
that their bytes equal installed version 1.2.3. Each actual experiment
must hash and report its installed aircraft/system/script assets. The
control-response runner records hashes of selected relevant XML inputs.
Further dependency-version matching and cross-platform stability checks are
still required before any paper-level provenance assertion.

## Current characterization experiment

The new `code/probe_control_responses.py` uses **independent fresh JSBSim
instances** for two unmodified baseline replays and paired `+0.06` /
`-0.06` normalized pilot-command perturbations for each of four controls.
The stock script remains active. Each trial starts the perturbation after
45 simulated seconds, observes 2 simulated seconds, and logs command
readback, final command, actuator output and selected state measurements.
It requires equal pre-perturbation states and hashes between trials.
This experiment is a *local, coupled, transient script-state comparison*,
not an independent control-sign certification or hover trim.

Possible outcomes: finite MONOTONE response, no measurable response,
nonmonotone/drifting response or an unresolved simulation/backend error.
The result must not be tuned into a favorable pass; retain negative
observations and code/asset provenance.

## Outstanding validation gates

1. Validate control-direction conventions against rotor equations/documented
   frame definitions, separately from empirical short-run sensitivities.
2. Replace the stock flight script with controlled, documented model setup
   and a demonstrable trim or repeatable steady hover start.
3. Implement a measured, deterministic closed-loop **position** controller
   and log command/actuator saturation, yaw, north/east position and altitude.
4. Repeat at h, h/2 and h/4, keeping the controller/sensor clock unchanged.
5. Compare the model's behaviour to trustworthy published references;
   report any unsatisfied validation requirements, not implied real fidelity.
