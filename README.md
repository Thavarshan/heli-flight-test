# Helicopter Flight-Test Research

Working title: Replay-Stable Reduction of Helicopter Hover-Control Failure Scenarios.

Status: preliminary backend feasibility and exploratory hover stationarity screening. A pinned JSBSim AH-1S example runs headlessly and replays identically within the tested local environment; fixed-position hover is not yet validated. No helicopter backend, autopilot, experimental results, or novelty claim has been validated yet. No AI/ML or model training is planned.

See [preliminary feasibility](docs/guides/FEASIBILITY.md) and `code/probe_backend.py` for the first executable milestone.

## Research and submission direction

See [selected topic](docs/guides/RESEARCH_TOPIC.md), [closest prior work](docs/guides/RELATED_WORK.md), and [submission plan](docs/guides/SUBMISSION_PLAN.md). The planning target is ICUAS 2027; the proposal and evidence are not submission-ready. The main contribution under investigation is replay-aware scenario reduction. Established search methods will generate the shared failure corpus.

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

The research experiment runner deliberately cannot execute scientific flights yet. First follow `docs/guides/ROADMAP.md`. Final experiment execution must save resolved configuration, source revision, backend/model hashes, environment, seed, trajectories and metrics. Resume only when all provenance matches.

The preliminary AH-1S probe can now produce an auditable, non-scientific
stationarity screen (it does **not** establish fixed-position hover). With
the pinned Python dependencies installed:

```sh
python -m pip install -r requirements-probe.txt
python -m unittest discover -s tests -v
python code/probe_backend.py --seconds 45 --output smoke-output/jsbsim-probe.json
python docs/scripts/check_probe_report.py --report smoke-output/jsbsim-probe.json
```

The report, its separate trajectory JSON, exact-replay flag and hashes are
verified together. `PASS_CANDIDATE` only indicates the defined exploratory
stationarity limits were met; it cannot replace trim/model validation, physical
flight evidence or the scientific protocol. The GitHub Actions smoke job
uploads preliminary evidence artifacts.

Paper compilation, once LaTeX is installed:
```sh
cd docs/paper
pdflatex Research-Paper.tex
bibtex Research-Paper
pdflatex Research-Paper.tex
pdflatex Research-Paper.tex
```

The paper uses the portal-recommended class, preserved with upstream notices; see docs/paper/TEMPLATE_PROVENANCE.md. The submission plan records verified requirements and remaining manual checks. This project is simulation research; physical flight performance is outside its current evidence.

Local paper checks (compiled PDF optional):
```sh
python docs/scripts/check_submission.py
python docs/scripts/check_submission.py --pdf work/Research-Paper.pdf
```
These check selected formatting/anonymity indicators, not scientific readiness or complete venue compliance. The official portal PDF test remains required.

## Exploratory model/control investigation (not flight validation)

The separate control-response probe compares paired fresh-instance pilot
control perturbations **while the stock AFCS and script remain active**:

```sh
python -m pip install -r requirements-probe.txt
python -m unittest discover -s tests -v
python code/probe_control_responses.py --output smoke-output/control-responses.json
```

The resulting JSON records controls, actuator responses, state differences and
selected model file hashes. It is **not** a calibrated hover controller and
must not be interpreted as proof of sign, trim, rotorcraft fidelity or safety.
See [model audit](docs/guides/MODEL_AUDIT.md) and the linked research gates.
