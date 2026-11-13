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
