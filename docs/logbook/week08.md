# Logbook — Week 8 (7 to 13 Dec 2026): confidence model v1 and sealed test set ★ M4

## Exit gate

| Condition | Status | Evidence |
|---|---|---|
| Confidence model and calibration reproducible by one command | **green** | `python tasks.py reproduce`; two runs give identical numbers (XGBoost pinned to one thread) |
| Second member reproduces the model results | **pending (human)** | Command ready; needs a teammate to run it |
| At least 600 labels, 150 double-labelled; kappa ≥ 0.6 or adjudicated and reported | **red** | Reviewers set aside (2026-10-20). Agreement code ready (`ai/evaluation/agreement.py`) |
| Locked test sealed | **green** | `data/annotation/locked_test_seal.json` (250 tickets, SHA-256 `608c0d37…`); CI fails if anything reads it before Week 10 |

`v0.4` is not tagged: the label conditions are not met.

## Results (PROVISIONAL: LLM-judge labels, validation split, 135 drafts)

| Model | Val AURC | AUROC (unacceptable) |
|---|---|---|
| Best single baseline (B4, top-1 similarity) | 0.173 | 0.644 |
| B7 (logistic regression on B4 + B5 + B6) | 0.180 | 0.625 |
| Logistic regression, all signals | 0.257 | — |
| **XGBoost, all signals (chosen)** | **0.149** | **0.656** |

Calibration: Platt scaling on the calibration split (isotonic was tried first; its ties raised AURC from 0.151 to 0.187).

### Lane thresholds (Learn then Test, delta 0.10, pre-specified grid)

| Lane | Budget | Certified threshold | Validation |
|---|---|---|---|
| Fast | 10% | none (lane closed) | — |
| Assisted | 40% | 0.05 | 86% shown, 20.7% unacceptable |
| On the unseen split | — | — | 53% of drafts reach the assisted lane, **all unacceptable** |

Coverage the admin can buy per budget: nothing below a 40% budget on the current calibration labels.

### Ablations (drop one group; positive = the group helped)

| Group | ΔAURC [95% CI] |
|---|---|
| routing | +0.066 [+0.022, +0.117] |
| category history | +0.049 [+0.012, +0.105] |
| ticket | +0.027 [+0.004, +0.062] |
| cross-department probe | +0.024 [+0.005, +0.052] |
| reranker | +0.013 [−0.003, +0.035] |
| grounding | −0.004 [−0.027, +0.019] |
| consistency | −0.014 [−0.033, −0.001] |
| retrieval | −0.015 [−0.036, +0.001] |
| evidence quality | −0.020 [−0.041, −0.006] |

### Agreement so far

Rishikesh's 30 pilot labels against the LLM judge: 82% agreement on acceptable or not (kappa 0.58), 43% on the exact A/M/R/W label (kappa 0.20, linear-weighted 0.46). The judge is usable for the binary target, not for the four-way grade.

## Rishikesh
- Gate service: versioned thresholds in the database (one active set), every draft's lane, score and reasons logged; `GET /tickets/{id}/decision`; loader that certifies a threshold set from a training report.
- Training and evaluation refuse to run if the benchmark freeze or the locked-test seal no longer verifies.

## Aashritha
- Error Budget admin screen (active thresholds, coverage per budget, history, provisional warning).
- Lane, score and reasons on every draft in the workbench; kappa, weighted kappa and Fleiss' kappa.

## Shivaganesh
- Dataset loader with a named label source and a logged locked-test guard; confidence model (logistic regression and XGBoost, group-aware CV, category history from training labels only, top reasons); Platt calibration; pre-specified LTT grid; ablations; locked-test seal; one-command reproduce.

## Findings
- **Fixed-sequence LTT needs a coarse grid.** Testing every distinct score ended the sequence at the first tiny test (one error among the five most confident drafts), certifying nothing. A grid fixed in advance (0.99, 0.95, …, 0.05) avoids it.
- **The guarantee does not transfer to unseen topics** (H3): thresholds certified on known topics let unseen-topic failures into the assisted lane. The Week 9 gate needs a shift guard (the probe, and an abstain rule for weak routing).
- **Some signal groups hurt** on judge labels (evidence quality, consistency). Re-run on human labels before removing anything.
