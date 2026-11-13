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
