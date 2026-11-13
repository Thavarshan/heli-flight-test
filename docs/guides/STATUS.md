# Current status — 2026-11-13

Completed: scaffold; initial primary-source prior-art screen; backend comparison; isolated Python 3.11 environment; pinned JSBSim feasibility probe. Upstream AH-1S scripted flight ran 60 simulated seconds with finite logged state and exact replay between two fresh instances. Evidence: results/preliminary/jsbsim-probe.json. See FEASIBILITY.md for reproduction and limits.

Provisional backend: JSBSim for investigation, pending hover/model validation. ArduPilot source/docs inspected; not built or executed.

Not completed: systematic novelty review, model fidelity validation, fixed-position hover controller, timestep convergence, fault injection, search/reduction algorithms, confirmatory experiments, completed paper.

Next: inspect AH-1S trim and controller assets; establish repeatable fixed-position hover and validation checks. Do not interpret the upstream demonstration as stable position hold. Freeze no scientific settings yet.

## Topic and submission planning update
Selected research direction: replay-stable reduction of helicopter hover-control failure scenarios, conditional on novelty/pilot validation. Primary planning venue: ICUAS 2027 contributed paper. Added focused related-work comparison, venue/rules/timeline, AI-use ledger, manuscript outline with verified references and official template provenance, .editorconfig and local submission checks. See RESEARCH_TOPIC.md and SUBMISSION_PLAN.md. Existing local formatting edits to interfaces.py and probe_backend.py were preserved.

Next implementation milestone is unchanged: validated fixed-position hover. In parallel, complete the closest-method comparison before claiming the reduction predicate is novel. No author list, travel arrangement, registration or submission has been finalized.

Verification: local scaffold/source checks and Python compilation passed. The manuscript compiled with BibTeX; its one-page proposal PDF passed local page-size, font-embedding and Author-metadata checks and was visually inspected. This does not establish scientific or full submission compliance.

## 2026-11-13 implementation update (preliminary, not validated)
- Added a pure-Python fail-closed stationarity screen with explicit SI conversions,
  body-speed, start-relative horizontal excursion, altitude band, attitude, rotor
  RPM and trajectory-integrity checks. Thresholds are exploratory development
  screening limits, **not** predeclared scientific requirements or stable hover.
- Instrumented the upstream JSBSim AH-1S demonstration to record north/east
  displacement and rotor speed alongside state, preserving the original script
  variant 1 and fresh-instance replay comparison. Writes reports atomically.
- Added Python standard-library tests, a trajectory/hash rechecker, and a
  free public-repository GitHub Actions smoke job with short-lived evidence artifacts.
- All initial work is on `research/hover-validation-mvp-20261113`; CI must
  finish successfully before merging. No claim of an experimentally demonstrated
  fixed-position hover, validated aircraft model, or paper result is made.

Next scientific blocking step: understand AH-1S model/control signs and
build a genuinely closed-loop fixed-position hover controller. Validate nominal
hover against independent published behaviour and at h / h/2 / h/4 before
freezing gusts or delay, or running confirmatory failure reduction.

## 2026-11-13 measured smoke-run evidence
The pinned Linux JSBSim demonstration ran 6,000 steps and replayed exactly, but
the last 20 s did not meet the exploratory hover screen (42.35 m horizontal
excursion, 10.59 m AGL altitude variation). See
`results/preliminary/2026-11-13-ah1s-stationarity.md` and the linked CI
run. This is a **negative preliminary observation** and further confirms that
fixed-position hover is still the blocking scientific milestone.

## 2026-11-13 follow-on: control-response investigation
A separate feature branch `research/control-response-audit-20261113`
adds a paired open-loop control-response runner, offline response classifier
tests, a GitHub Actions evidence artifact and the AH-1S model license/limitations
audit. CI results and any observed local response must be recorded before
calling the work completed; nothing here is stable fixed-position hover.
See `docs/guides/MODEL_AUDIT.md`.

Important source clarification: the AH-1S aircraft **model** header declares
GPL with a conditional alternative CC-BY-NC-SA route and admits use of
estimates; JSBSim engine LGPL licensing does not determine the model license.
No aircraft/model source is being redistributed in this repository.

## 2026-11-13 development-only position-feedback pilot (not stable hover)
The independent fresh-instance control-response test succeeded in [CI
#43403687934](https://github.com/Thavarshan/heli-flight-test/actions/runs/43403687934).
Each of the four pilot commands produced measurable transient actuator
response. In the selected 2 s window and primary readouts, the paired
response signs were + collective-altitude, - longitudinal-pitch-rate,
+ lateral-roll-rate, + pedal-yaw-rate. This is a property of one
scripted flight state, not an independently validated sign convention.

A second reproducible trial in [CI #43403867980](https://github.com/Thavarshan/heli-flight-test/actions/runs/43403867980)
compared a heuristic bounded perfect-state position feedback against an
unchanged stock-script arm, both from the same state at t=45 s for the
following 25 simulated seconds. The pre-validation experiment yielded:
- Uncontrolled final horizontal drift from t=45 target: 35.688 m;
  sampled horizontal RMS error: 20.051 m.
- Initial feedback controller final drift: 35.300 m;
  sampled horizontal RMS error: 16.879 m.
- Fresh-instance replay of the feedback run was exact on this runner.
- Recorded command-overwrite step count: 0 for this specific window.

These observations **do not establish stationary hover or reliable
improvement**, because the aircraft begins with drift, the stock script
and AFCS remain active, gains were an unvalidated first proposal, and
neither controller stability nor model fidelity was independently
verified. These are not confirmatory samples, not a paper result, and
not a general claim that the method works. Retain the complete
artifacts and this negative end-drift observation. The original
[hover gate #2](https://github.com/Thavarshan/heli-flight-test/issues/2)
remains open. Next: isolate a reproducible steady hover initial state,
remove stock scripted flight events from the controlled phase, validate
command signs and perform h/h2/h4 convergence tests.

## 2026-11-13 latest prior-art alert
A primary-source July 2026 arXiv preprint on stochastic, environment-aware
failure-preserving CPS delta debugging was located and added to
`RELATED_WORK.md`, `LITERATURE.md` and the provisional manuscript
bibliography. This establishes a **high overlap risk** for general
replay-aware reduction claims. The narrower step-size/physical-time
helicopter hypothesis is not a proven novel method, and the authors'
replication artifacts require inspection. The hover/model-validation
gate remains open.

## 2026-11-13 numerical/model-validation blocker (new experiments)

The next branch `research/numerical-convergence-gate-20261113` adds:
a same-physical-observation-clock JSBSim `h/h2/h4` script comparison;
an independent no-script model+IC initializer; a 16-case bounded SFD
informed seed sweep; and a fresh-replay 45s extension of the chosen
development seed. Each has a short-lived CI JSON artifact and explicit
unresolved/negative outcomes. All results are summarized with runner/CI
links in `results/preliminary/2026-11-13-timestep-gate.md`.

The stock flight demo differs substantially between h and h/4 (maximum
north position difference 76.25m, AGL difference 15.39m in this 45s case).
**Only the observation clock was fixed**; the built-in AFCS/event
evaluation rate changes with the integration timestep, so this is NOT
an isolated physics-convergence test. The independent script-free
75ft initialization almost reached the ground within 4.5s. The SFD-
informed 9s seed looked temporarily near-zero displacement, but the
full 45s followup failed the final-window hover screen for all timesteps
(in the h run, altitude span exceeded 107m). Fresh-instance replay was
exact within the tested environment.

**Decision:** model validation and stationary hover remain BLOCKED.
Next establish a demonstrable trim and a fixed physical-time controller
clock independent of integration step, then retest convergence and
hover before adding failures/reduction. Do not promote these observations
to published evidence of rotorcraft control stability.
