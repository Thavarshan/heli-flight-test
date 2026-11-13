# Focused prior-art review — 2026-11-02

This is a bounded primary-source review, not a systematic review or proof of absence. Search terms included helicopter hover falsification; counterexample reduction simulation; drone input minimization; timestep falsification; and gust sensor-delay controller testing. Full artifact reproduction remains pending.

| Work and inspected evidence | Relevant overlap | Consequence for this project |
| --- | --- | --- |
| [S-TaLiRo, TACAS 2011, primary paper](https://home.cs.colorado.edu/~srirams/papers/sTaliro-tacas11.pdf) — initial abstract/method screen | Temporal-logic falsification via simulation is established | Use established search as a baseline; no generic falsification novelty claim |
| [Ernst et al., Time-Staging Enhancement, EPTCS 361 (2022), pp. 25–43](https://arxiv.org/abs/1803.03866v2) — verified version metadata and abstract | Constructs candidate signals incrementally over time intervals | Timing-aware search alone is not our contribution; inspect the complete algorithm before implementing related guidance |
| [Singh and Saha, Specification Guided Automated Debugging of CPS Models (2020), author manuscript](https://www.cse.iitk.ac.in/users/isaha/Publications/Journals/TCAD20.pdf/) — abstract and helicopter case, pp. 8–10 | Signal localization and parameter repair; includes a small helicopter angular-velocity benchmark | Helicopter control debugging already exists. Our proposed full flight-dynamics scenario reduction is distinct in scope, but this does not prove novelty |
| [Wang et al., ADGFUZZ, NDSS 2026](https://www.ndss-symposium.org/wp-content/uploads/2026-s1014-paper.pdf) — abstract, Sec. IV-F and evaluation setup | Robotic-vehicle fuzzing includes simulator reinitialization and input removal to preserve bug triggering; evaluates quadcopter, plane and rover | Strong overlap with failure minimization. A new helicopter application or deletion loop alone is insufficient. Compare our replay-set predicate and continuous physical-time reduction against its minimization process |
| [Search-based Software Testing for Drone Applications: An Experience with the Simulink Environment (2026), publisher text](https://link.springer.com/chapter/10.1007/978-3-032-22774-4_16) — method/evaluation sections | Uses S-TaLiRo with uniform random and simulated annealing on drone controllers | Drone controller testing is established; compare conventional non-learning optimizers |
| [Narducci and Hariharan, A Common Simulation for Hover Validation of a Helicopter near the Ground, AIAA 2023-1187](https://doi.org/10.2514/6.2023-1187) — abstract | Discusses shared hover scenarios and limited public helicopter validation data | A runnable model is not experimentally validated; published scenario agreement also is not physical truth |

## Required follow-through before novelty freeze
Read complete reduction/falsification methods and citation trails, especially ADGFUZZ, delta debugging, numerical sensitivity, and robust counterexample simplification. Record exact failure-preservation predicates, reduction grammars, reset semantics, and evaluation units. Investigate [Simplifying and Isolating Failure-Inducing Input](https://doi.org/10.1109/32.988498) as the foundational delta-debugging baseline; full text was not retrieved in this session. Do not claim a new delta-debugging algorithm.

Candidate gap to test: whether retaining the same hover violation across a declared numerical replay set during continuous-input reduction yields a useful simplicity/retention/cost trade-off. This remains an inference from the inspected subset. No accepted-paper outcome is promised.

## 2026-11-13 novelty-alert update (important overlap)

1. **Valle, Ali and Arrieta, [*Delta Debugging for Cyber-Physical Systems
   with Flaky Test Executions*](https://arxiv.org/abs/2607.25695)
   (arXiv preprint posted 28 July 2026).** Inspected abstract, method
   overview and introduction in the primary full-text rendering.
   The authors formulate failure clustering and **repeated statistical
   execution-based preservation** for CPS input reduction, with optimized
   and environment-aware variants, and evaluate on a stochastic elevator
   controller and simulated mobile robot. Their reported observation
   that reduced inputs may reproduce failures *more* reliably is
   directly relevant to our working replay-retention hypothesis.
   **Novelty risk: HIGH** for any broad claim that replay-aware
   failure-preserving CPS input minimization is new. The possible narrower
   distinction is deterministic *physical-time gust/sensor-delay*
   reduction subjected to *specified integrator step-size and held-out
   initial-state replays* on a validated conventional helicopter hover
   system. Whether that distinction is sufficient remains **unknown**
   until full-method/reproduction comparison, validated hover and pilot
   experiments. The source is currently a **preprint**; do not imply
   journal or conference peer review.
2. **[*Towards the Isolation of Failure-Inducing Inputs in
   Cyber-Physical Systems: is Delta Debugging Enough?*](https://doi.org/10.1109/SANER53432.2022.00072),
   SANER 2022.** Publisher abstract inspected, not full artifact.
   The work already adapts delta debugging to Simulink CPS failures and
   studies three models. Therefore CPS delta-debugging adaptation is
   clearly established; read its full method before finalizing baselines.
3. **Zeller and Hildebrandt,
   [*Simplifying and Isolating Failure-Inducing Input: A Retrospective
   on Delta Debugging*](https://cispa.de/en/research/publications/84689-simplifying-and-isolating-failure-inducing-input-a-retrospective-on-delta-debugging),
   institutional publication page (2025).** Publication page/summary
   inspected, not the entire full paper. General DD and input
   minimization remain established foundations rather than our novelty.

### Required protocol change before confirmatory freeze
Include *statistical repeated-run and environment-aware reduction* as
a close-method comparator or explain its infeasibility with a transparent
cost model. The final research question must distinguish **deterministic
numerical discretization sensitivity** from **stochastic test flakiness**.
Do not describe fresh-instance byte-identical replay as stochastic
robustness. Inspect the 2026 preprint's exact acceptance and cost
accounting and evaluate its publicly reported replication materials
before publishing a method novelty claim. This is a novelty-risk warning,
**not a conclusion that the proposed method is already identical**.
