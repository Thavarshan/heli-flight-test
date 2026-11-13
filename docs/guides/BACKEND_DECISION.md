# Model/backend decision record — 2026-11-13 (open)

## Present decision

**Do not proceed to confirmatory testing with the AH-1S yet.**
Keep JSBSim v1.2.3 and its installed AH-1S example as a research
feasibility testbed, not an airplane/helicopter simulator validated by
this project. The current full 45-second SFD-informed no-script
candidate fails exploratory hover stationarity at all three tested
integration timesteps. The stock event script is numerically sensitive,
and its AFCS controller update schedule varies with integrator step.

This is a **blocker to the current scientific experiment**, not proof
that JSBSim or the aircraft model is inherently unsuited to hover, and
not license to present negative development runs as controller failures.

## Alternatives and primary-source evidence

| Candidate | Evidence checked | Good reason to explore | Unresolved before scientific adoption |
| --- | --- | --- | --- |
| Existing JSBSim AH-1S | [Aircraft and model notes](https://github.com/JSBSim-Team/jsbsim/blob/master/aircraft/ah1s/ah1s.xml); [steady-flight tables](https://github.com/JSBSim-Team/jsbsim/blob/master/aircraft/ah1s/Systems/steady_flight_data.xml); reproducible project CI | Lightweight, in-process, headless, fast deterministic replay | Stable trim, independently controlled feedback rate, step convergence and external model validation; author explicitly describes estimates and limited validation |
| ArduPilot conventional-helicopter SITL | [Conventional helicopter dynamics](https://github.com/ArduPilot/ardupilot/blob/master/libraries/SITL/SIM_Helicopter.cpp); [SITL documentation](https://ardupilot.org/dev/docs/sitl-simulator-software-in-the-loop.html) | Integrated flight controller and a concrete conventional-rotor model, including yaw and collective channels; possible reliable position-hold *testbed* | Build/run verification, deterministic reset/clock semantics, sensor delay API, full provenance, simplified SITL physics and independently checked fidelity. A stabilized autopilot in SITL is not flight-test validation |
| Texas A&M TRAC UH-60 model | [University research page](https://avfl.engr.tamu.edu/projects/helicopter-flight-dynamics-code/); [2020 research paper](https://arxiv.org/abs/2008.09873) | Describes a hover-trim-capable rotorcraft dynamics package whose authors compared trim against UH-60 test data | Downloadable source and license **not verified**; installation, performance, reproduction and model applicability remain unknown. Do not assume it is open source just because a paper describes the code |

## Practical go/no-go sequence

1. **First**, attempt a scientifically documented JSBSim hover trim using
   official dynamics/initial-condition APIs and known source-model settings.
   Stop if it cannot hold north/east/AGL with finite rotor speed and
   independently verified control directions.
2. **Then**, explicitly separate controller/sensor/event execution clock
   from physics integration. Run identical physical-time inputs at
   `h`, `h/2`, `h/4` and choose numeric tolerance from documented
   pilot precision. Different control update schedules cannot be
   interpreted as a convergence comparison.
3. **If the first two fail**, evaluate ArduPilot conventional-helicopter
   SITL with an actual tested build and scripted hover regression; do not
   import its assumptions wholesale as more physically realistic.
4. Consider TRAC only if code access, redistribution rights, practical
   integration and reproducible published hover-validation conditions
   can be independently verified.
5. Do not change research claims, primary model or target submission
   date without a documented pivot decision after comparable evidence.

## Model integrity
- JSBSim engine and aircraft asset licenses differ; see MODEL_AUDIT.md.
- No real-aircraft or manufacturer performance claim can be inferred
  merely from a working simulation.
- All outputs remain *preliminary* and no confirmatory corpus is frozen.

This record intentionally makes **no binary backend selection yet**.
