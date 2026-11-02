# Proposed study protocol — not preregistered

## Question
Under equal simulation budgets, can targeted search discover and reduce hover-control failures more efficiently than random sampling and a fixed grid?

## Candidate contribution
A search-and-reduction method exploiting disturbance timing and controller response. Novelty remains unverified. A generic simulator wrapper alone is insufficient.

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
