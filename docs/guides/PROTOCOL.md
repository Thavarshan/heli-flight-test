# Proposed study protocol — not preregistered

## Question
Under matched simulation budgets, does replay-aware scenario reduction preserve the same helicopter hover-control violation more reliably on held-out numerical replay conditions than nominal-only reduction?

## Candidate contribution
A reduction acceptance predicate using a declared numerical replay set, evaluated for simplicity, retention and cost. See RESEARCH_TOPIC.md for the current selected direction. Generic search supports corpus construction; a novel search optimizer is no longer the primary contribution. Novelty remains unverified.

## Initial scope
One conventional helicopter model; fixed-position hover; fixed controller; gust amplitude/direction/onset/duration and sensor delay. Choose numerical ranges only after model validation and a development pilot. Faults must be injected at documented interfaces, with correct physical units. Delayed measurements retain timestamps; never silently substitute delayed true state into the physics.

## Comparisons
Uniform random search, fixed grid, and proposed targeted search. Include a standard optimization baseline if literature review establishes it as necessary. Equal simulator-call budgets; additionally report simulated seconds and wall time. Count initialization, rejected and failed calls transparently. Reduction has a separately reported budget. Predefine grid ordering and handling of incomplete grids.

## Outcomes
Primary: probability of finding a qualifying failure within a fixed budget. Secondary: calls to first failure (right-censored when none), peak/RMS position error, heading error, saturation duration, and reduction cost/size. Define thresholds, dwell durations, warmup and finite horizon before evaluation. Record nonfinite states and backend errors separately.

## Repetition and analysis
Pair methods by initial condition and disturbance-family block. Use independent search seeds; choose sample size after pilot precision/power analysis. Bootstrap at independent replicate/block level, never timestep level. Report paired effect sizes and confidence intervals. Retain unsuccessful searches; avoid averaging discovery time over successful searches only. Correct multiple comparisons or identify exploratory outcomes.

## Validation gate
Document model provenance/license, hover trim, control signs, force/moment sanity, timestep convergence, reset/replay reproducibility and comparison with published reference behaviour. Demonstrate stable nominal hover before injecting disturbances. Assess whether discovered cases survive timestep and parameter perturbations. Simulator-only results do not establish real-aircraft behaviour.

## Ablations
Search without response-informed guidance; reduction disabled; individual disturbances versus their combination. Avoid counting repeated versions of the same failure as independent discoveries; define failure grouping in advance.

## Paper gate
Related-work gap verified; protocol frozen; validation documented; raw evidence and provenance available; figures/tables regenerated; claims audited against evidence.

## Decision amendment — 2026-11-02
RESEARCH_TOPIC.md specifies the revised primary/secondary research questions and reduction baselines. SUBMISSION_PLAN.md selects the planning venue. The preceding search comparisons are supporting corpus-generation analysis, not the primary hypothesis. Neither these documents nor configs/pilot.json are a frozen confirmatory protocol. Pilot thresholds, sample size and budgets remain unresolved.

## 2026-11-13 safety gate amendment
The preliminary `h/h2/h4` probe fixed only **observation times**, not
AFCS/controller execution times. This is not a valid convergence check.
Before fault injection, freeze a controller/sensor scheduler with an
independent physical-time clock and verify it does not change under
integrator refinement. Separate physics-only, controller, model-source
and disturbance-event effects in numerical sensitivity diagnostics.
Do not interpret `UNRESOLVED` as a satisfied failure predicate.

## 2026-11-14 backend-selection amendment (pilot only)

If the ArduPilot conventional-helicopter SITL is adopted, update the
research airframe class from modeled AH-1S to the small ~4.54 kg
conventional helicopter in the pinned ArduPilot SITL source, and do
not retain aircraft-specific performance or controller claims across
backends. The first necessary positive evidence is helicopter-specific
firmware, valid GPS position and motor interlock/rotor-runup before a
**measured** stationary position-hold gate. A green CI test that simply
launches the process does not satisfy this gate. No disturbance or
scenario-reduction confirmatory experiment is authorized until the new
backend passes fixed-clock, true-state and replay validation separately.
