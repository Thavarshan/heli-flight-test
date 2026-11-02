# Current status — 2026-11-02

Completed: scaffold; initial primary-source prior-art screen; backend comparison; isolated Python 3.11 environment; pinned JSBSim feasibility probe. Upstream AH-1S scripted flight ran 60 simulated seconds with finite logged state and exact replay between two fresh instances. Evidence: results/preliminary/jsbsim-probe.json. See FEASIBILITY.md for reproduction and limits.

Provisional backend: JSBSim for investigation, pending hover/model validation. ArduPilot source/docs inspected; not built or executed.

Not completed: systematic novelty review, model fidelity validation, fixed-position hover controller, timestep convergence, fault injection, search/reduction algorithms, confirmatory experiments, completed paper.

Next: inspect AH-1S trim and controller assets; establish repeatable fixed-position hover and validation checks. Do not interpret the upstream demonstration as stable position hold. Freeze no scientific settings yet.

## Topic and submission planning update
Selected research direction: replay-stable reduction of helicopter hover-control failure scenarios, conditional on novelty/pilot validation. Primary planning venue: ICUAS 2027 contributed paper. Added focused related-work comparison, venue/rules/timeline, AI-use ledger, manuscript outline with verified references and official template provenance, .editorconfig and local submission checks. See RESEARCH_TOPIC.md and SUBMISSION_PLAN.md. Existing local formatting edits to interfaces.py and probe_backend.py were preserved.

Next implementation milestone is unchanged: validated fixed-position hover. In parallel, complete the closest-method comparison before claiming the reduction predicate is novel. No author list, travel arrangement, registration or submission has been finalized.

Verification: local scaffold/source checks and Python compilation passed. The manuscript compiled with BibTeX; its one-page proposal PDF passed local page-size, font-embedding and Author-metadata checks and was visually inspected. This does not establish scientific or full submission compliance.
