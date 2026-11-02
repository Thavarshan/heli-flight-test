# Codex project instructions

## Objective
Develop reproducible software research on conventional main-rotor/tail-rotor helicopter hover-control testing. No AI/ML, training, or large datasets.

## Research integrity
- Read README, protocol, literature ledger and STATUS before work. Update STATUS after meaningful progress.
- Never fabricate results, references, novelty, simulator fidelity, or completed checks.
- Distinguish proposals, pilot observations and confirmatory findings.
- Validate model trim, coordinate frames, units, control directions and numerical convergence before using trajectories as research evidence.
- A simulator's rotor support does not establish validity of an aircraft model or fault mechanism.
- Freeze controller tuning, search parameters, thresholds and evaluation protocol before confirmatory runs. Separate development scenarios from evaluation scenarios.
- Keep negative results and failed runs. Numerical/backend errors are not automatically controller failures.
- Every empirical paper claim must link to a reproducible result artifact or verified reference. Never copy numerical results into instructions as permanent truth.

## Implementation
Use code/heli_lib for reusable components and thin command-line runners. Record SI units and frame conventions. Use deterministic seeds and isolated simulation state. Hash full resolved configs and model assets; do not resume from filename existence alone. Write results atomically. Test reset independence, delayed-sensor semantics, failure predicates and replay determinism.

## Writing
Use concise formal English and LaTeX. Research-Paper.tex is manuscript source of truth. Generate tables/figures from recorded results; keep exploratory output separate. Report effect sizes, uncertainty, compute budgets and limitations. Verify citations from primary sources. Verify venue format, anonymization and AI disclosure policy when a venue is selected. No checker can certify plagiarism absence or universal policy compliance.

## Scope
First implement and validate one helicopter backend and stable hover. Then add wind gusts and sensor delay. Autopilot novelty, full flight envelopes, autorotation and real hardware are later scope decisions.

## Current research/venue decision
Read RESEARCH_TOPIC.md, RELATED_WORK.md, SUBMISSION_PLAN.md and AI_USAGE.md in docs/guides. The primary hypothesis now concerns replay-aware reduction, not a novel general search algorithm. ICUAS 2027 is the planning target. Use the recorded anonymous-review rules and page budget; recheck official sources before submission. Keep all claims provisional until the validation, novelty and confirmatory-study gates pass. Retain the public development repo but never use its identifying URL in the anonymous submission. Maintain the AI-use record honestly.
