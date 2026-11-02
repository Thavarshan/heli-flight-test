# Research decision — 2026-11-02

## Selected direction
**Replay-Stable Reduction of Helicopter Hover-Control Failure Scenarios**.

Build a simulation-based testing tool for a conventional main-rotor/tail-rotor helicopter hover controller. Discover failing gust/delay scenarios using established search, then reduce those scenarios while retaining the same violation across declared replay conditions. This replaces the broad ambition of inventing an entire simulator/autopilot/search framework at once.

The scientific contribution is a proposed reduction acceptance rule and an empirical evaluation of its trade-off between scenario simplicity, replay retention and simulation cost. Novelty is conditional on the literature and pilot gates below. Do not describe it as the first helicopter falsifier, a globally minimal reproducer, root-cause identification, or physical safety verification.

## Why this direction
Closest work already contains control falsification, helicopter-model debugging and robotic-vehicle input minimization; see RELATED_WORK.md. A helicopter wrapper alone is insufficient. Our candidate distinction is retaining a declared failure signature while reducing continuous gust/delay inputs under explicitly controlled numerical replay conditions. This is a research hypothesis, not a confirmed gap.

## Proposed method
Represent each scenario as bounded smooth gust pulses plus timestamped sensor-delay intervals. Preserve physical-time event semantics as the physics timestep changes. Keep sensor sampling and controller update periods fixed when refining the integration timestep, so we do not conflate a different controller with a different integrator.

Use event deletion followed by bounded duration/amplitude/delay shrinking. Accept a candidate only when: (1) it stays in the admissible input grammar, (2) the same predeclared requirement is violated for a minimum dwell duration, (3) it retains a chosen violation margin, and (4) it passes the declared replay set. Evaluate all returned candidates independently, including baseline outputs, using the same held-out replay suite. Held-out results must not feed reduction decisions.

Development replay candidates: fresh initialization and integration timesteps h and h/2. Held-out assessment: h/4 and separately reported small initial-condition perturbations selected before evaluation. These are proposed settings, not evidence that such checks improve practical outcomes. Repeated identical deterministic replays alone do not establish robustness. No stochastic model learning is involved.

Simplify lexicographically: event count, active disturbance duration, then normalized disturbance magnitude. Always report individual dimensions. Do not shrink failure by changing the aircraft, controller, requirement, horizon, initial trim or normalization bounds. Delay semantics and interpolation policy must remain explicit. Allow UNRESOLVED/backend-error outcomes.

## Questions
- RQ1 (primary): Does replay-aware acceptance improve held-out retention of the same violation relative to nominal-only reduction at matched simulation cost?
- RQ2: What simplicity is achievable, and at what cost, compared with unchanged scenarios, event-only delta debugging, and nominal-only event/parameter shrinking?
- RQ3 (secondary): Which retained cases require gust and delay jointly, rather than either input separately? Removing an input is an intervention in this model, not proof of a physical root cause.

Use common initial failure cases from frozen uniform-random and differential-evolution search. Search performance is supporting analysis, not the central novelty claim. Fixed grids remain a descriptive baseline if dimension permits. Include an independent nominal-only reducer with the same total call allowance as the proposed method. Count every replay call and simulated second; charge failed calls. Add a post-hoc replay-validation baseline to separate validation benefit from reduction decisions.

## Evidence needed
One model with documented provenance and nominal hover, control-sign/unit checks, and timestep convergence. At least two meaningfully different conventional controller configurations (not presented as independent aircraft); a second controller design/model is a stretch goal. Do not use deliberately bad tuning as the only failure source. Report a single-model external-validity limitation.

Freeze a shared evaluation corpus of unique failure cases from development-independent search seeds. Include every case's reduction outcome; report the subset already replay-stable before reduction separately. If a reducer returns nothing, count that outcome rather than excluding it. Pair methods by original case; cluster uncertainty estimates by independent source search run, not timestep or derivative case. Determine sample size and budgets from pilot precision, then freeze protocol. Save signed margins, dwell times and matched violation identifiers, not merely a crash flag.

## Gates and pivot
1. By 2026-11-20: stable hover and model-validation evidence, plus detailed comparison with closest reduction methods. If unavailable, reconsider backend/scope.
2. By 2026-12-11: pilot demonstrates admissible nontrivial failures and enough cases to evaluate retention. If nominal reduction never loses replay validity, report that observation and reconsider the method hypothesis instead of manufacturing fragile cases.
3. By 2026-12-18: freeze confirmatory protocol and source versions. If related work already implements the same idea, pivot to a clearly scoped replication/benchmark study or select a different contribution.

These dates are internal targets. The AH-1S package is a simulation testbed candidate, not a validated unmanned helicopter or a real-flight dataset. Model validation is still the first implementation milestone.
