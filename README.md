# Helicopter Flight-Test Research

Working title: Search-Based Discovery and Reduction of Helicopter Hover-Control Failures in Simulation.

Status: preliminary backend feasibility. A pinned JSBSim AH-1S example runs headlessly and replays identically within the tested local environment; fixed-position hover is not yet validated. No helicopter backend, autopilot, experimental results, or novelty claim has been validated yet. No AI/ML or model training is planned.

See [preliminary feasibility](docs/guides/FEASIBILITY.md) and `code/probe_backend.py` for the first executable milestone.

## Workflow
Research → model validation → baseline hover → fault injection → search comparison → failure reduction → statistics → paper.

This follows the code/results/docs/tests and experiment-to-paper workflow in https://github.com/Thavarshan/dinov2-ssl-cifar, adapted without copying its implementation or findings.

## Layout
- `code/heli_lib/`: simulator interface and future reusable implementation
- `code/run_experiment.py`: experiment plan validation and dry-run manifest
- `configs/pilot.json`: initial study specification
- `results/`: generated evidence, never invented findings
- `docs/guides/`: protocol, roadmap, literature ledger, progress
- `docs/paper/Research-Paper.tex`: manuscript source
- `docs/scripts/check_project.py`: scaffold integrity checks
- `tests/`: implementation tests as meaningful components are added
- `.github/workflows/checks.yml`: scaffold checks
- `AGENTS.md`: Codex research and writing rules

## Start
Python 3.11+; scaffold uses the standard library only.

```sh
python code/run_experiment.py --config configs/pilot.json --dry-run
python docs/scripts/check_project.py
```

The runner deliberately cannot execute flights yet. First follow `docs/guides/ROADMAP.md`. Final experiment execution must save resolved configuration, source revision, backend/model hashes, environment, seed, trajectories and metrics. Resume only when all provenance matches.

Paper compilation, once LaTeX is installed:
```sh
cd docs/paper
pdflatex Research-Paper.tex
```

No venue or page limit has been selected. Select and verify these before adopting a submission template. This project is simulation research; physical flight performance is outside its current evidence.
