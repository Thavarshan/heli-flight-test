# Implementation roadmap

1. Literature and backend feasibility: compare JSBSim and ArduPilot helicopter simulation, model availability, license, fault interfaces, CPU runtime and documentation. Record selection rationale. Do not assume the two are directly integrated.
2. Model validation: trim and nominal hover, units/frames, control direction, timestep convergence and reproducibility. Stop the scientific evaluation if this gate fails.
3. Baseline controller: use an existing controller or implement a documented conventional controller. Tune only on development scenarios; freeze settings.
4. Experiment execution: implement isolated reset, faults, metrics, JSON metadata and trajectory output. Validate resume using configuration/source/model hashes.
5. Search and replay: implement random/grid first, targeted search next, then reduction with explicit replay checks.
6. Pilot: benchmark runtime and select budgets, sample size, thresholds and parameter bounds. Freeze confirmatory protocol.
7. Main study: run CPU batches, preserve artifacts, compute paired statistics, generate figures/tables.
8. Manuscript: write from evidence; verify target venue requirements; compile and visually inspect PDF.

CI initially checks the scaffold. Add smoke simulation and manually dispatched experiment matrices after the backend works. Upload immutable run artifacts; result commits can be added later if desired.
