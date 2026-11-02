# Literature and source ledger

Reference workflow inspected via connected GitHub on 2026-11-02:
- https://github.com/Thavarshan/dinov2-ssl-cifar/blob/main/README.md
- https://github.com/Thavarshan/dinov2-ssl-cifar/blob/main/code/run_experiment.py
- https://github.com/Thavarshan/dinov2-ssl-cifar/blob/main/.github/copilot-instructions.md

Starting sources from initial topic exploration; technical details must be read and verified before implementation or manuscript citation:
- JSBSim rotor API: https://jsbsim-team.github.io/jsbsim/classJSBSim_1_1FGRotor.html
- Candidate AH-1S model: https://github.com/JSBSim-Team/jsbsim/tree/master/aircraft/ah1s
- ArduPilot SITL: https://ardupilot.ardupilot.org/dev/docs/sitl-simulator-software-in-the-loop.html
- Helicopter/X-Plane connection: https://ardupilot.ardupilot.org/dev/docs/sitl-with-xplane.html
- UH-60 disturbance-rejection study: https://ntrs.nasa.gov/archive/nasa/casi.ntrs.nasa.gov/20000090530.pdf

Review queue: helicopter hover falsification; search-based control-system testing; temporal-logic robustness; simulation scenario minimization; rotorcraft model validation. For each paper record verified metadata, assumptions, baselines, artifacts and the precise difference from our proposal. No claim of an unfilled gap yet.

## Preliminary prior-art screen — 2026-11-02

- S-TaLiRo: A Tool for Temporal Logic Falsification for Hybrid Systems (TACAS 2011). Primary paper: https://home.cs.colorado.edu/~srirams/papers/sTaliro-tacas11.pdf . General simulation-based temporal-logic falsification is established; applying generic search to a helicopter is not by itself a verified new method. Full method comparison pending.
- Time-Staging Enhancement of Hybrid System Falsification (2018 preprint): https://arxiv.org/abs/1803.03866 . Abstract explicitly exploits temporal structure in optimization-based falsification. Timing-informed search therefore needs a detailed comparison, not a broad novelty claim.
- Automated Testing with Temporal Logic Specifications for Robotic Controllers using Adaptive Experiment Design (2021 preprint): https://arxiv.org/abs/2109.08071 . Related controller-testing work uses a surrogate model; inspect as prior art, but do not adopt model learning into this project.

These are an initial screen, not a systematic review. Next: inspect full methods and artifacts, helicopter-specific evaluations, non-learning optimizer baselines, and prior scenario reduction. Candidate contribution remains open: reproducible helicopter-specific benchmarks and a demonstrably different search/reduction method. Do not claim either contribution is novel yet.

## Focused review update
See RELATED_WORK.md for the current comparison, including prior helicopter-model debugging and robotic-vehicle input minimization. The selected hypothesis and novelty gates are in RESEARCH_TOPIC.md. Replace any claim that helicopter testing or failure reduction itself is new with a precise, evidenced method comparison.
