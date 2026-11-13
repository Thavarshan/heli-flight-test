# Verification status

Implemented: `tests/test_hover_metrics.py` exercises candidate screening,
drift, speed, ground/rotor rejection, missing telemetry, timestamps, invalid
values, incomplete traces and sparse sampling. Pure-Python; runs without JSBSim.

```sh
python -m unittest discover -s tests -v
```

`docs/scripts/check_probe_report.py` independently recalculates the
screen from the raw JSON trajectory and validates its SHA-256 and replay flag.

Outstanding: true controller reset independence, actuator-sign sanity,
timestep convergence (h, h/2, h/4), sensor timestamp/delay semantics, gust
injection, frozen failure predicates, model fidelity, and provenance-aware
experiment resume. Do not infer physics validation from these unit tests.

Added: pure-Python paired-response classification tests for both monotone
signs, nonmonotone response, no response, nonfinite data and input validation.
The JSBSim control-response runner is intentionally labeled exploratory.

Also implemented: `tests/test_hover_controller.py` checks the development
controller's frame transformation, nominal equilibrium, saturation, assumed
response directions, invalid input handling and altitude/climb terms.
These tests prove numerical behavior of code, **not** helicopter stability.

Added `tests/test_numerical_validation.py` with independent trace
comparison requirements: common physical-time grid, finite values, SI
units, expected columns, equal length and explicit UNRESOLVED status for
invalid traces. Model numeric results are intentionally descriptive.
