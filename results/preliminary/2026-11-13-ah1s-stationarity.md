# Preliminary AH-1S Linux smoke observation — 2026-11-13

**Status: feasibility only / FAIL_CANDIDATE. Not a validated hover experiment.**

Source run: [GitHub Actions #43400652366](https://github.com/Thavarshan/heli-flight-test/actions/runs/43400652366), `jsbsim-smoke` job, branch `research/hover-validation-mvp-20261113`, commit `bdda10a5b8edf372f4ef842af63292273488e058`. The source workflow also checks that raw trajectory JSON and report metrics agree; its 7-day artifact is not a permanent dataset.

## Execution

- Installed backend: JSBSim 1.2.3 on Linux x86_64, Python 3.11.18.
- Upstream `scripts/ah1s_flight_test.xml`, variant 1: staged flight / max-speed demonstration, **not fixed-position hold**.
- Duration: 45.00000000000151 simulation seconds; 6,000 integration steps.
- Two separately initialized runs had exactly identical logged trajectories on this runner.
- SHA-256 of JSON trajectory: `e38d8c20d4409a3f06ef3109d7dffa78e640ca2056309d5f67ca7067fc858ffc`.

## Final 20 s exploratory stationarity screen

| Indicator | Measured | Development-only screen condition | Screen |
| --- | ---: | ---: | --- |
| Peak body speed | 3.353 m/s | <= 1 m/s | Fail |
| North/east excursion relative to window start | 42.352 m | <= 3 m | Fail |
| AGL altitude span | 10.593 m | <= 2 m | Fail |
| Maximum absolute roll or pitch | 4.616 degrees | <= 10 degrees | Pass |
| Minimum AGL | 2.798 m | >= 5 m | Fail |
| Minimum rotor speed | 318.524 RPM | >= 1 RPM | Pass |

Overall: `FAIL_CANDIDATE`. This is an expected limitation of the upstream scripted flight, not a claim that a prospective hover controller failed. These screening limits are *not* validated aviation thresholds and are not frozen scientific failure requirements.

## Interpretation and next work

The probe now reliably rejects this demonstrably nonstationary scripted trajectory; it does **not** validate trim, rotorcraft dynamics, controller stability, real flight performance, or any failure-reduction hypothesis. Next implement a true fixed-position controlled hover, document control signs and model provenance, test reset and integration-step convergence, then define admissible gust/sensor-delay experiments. Preserve this negative observation as preliminary evidence rather than retuning the screen to manufacture success.
