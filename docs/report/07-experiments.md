# 7. Experiments

*Owners: Shivaganesh (7.1 to 7.6), Aashritha (7.7). Draft v1.*

> All numbers in 7.2 to 7.6 are **development numbers**: validation split, LLM-judge labels.
> The pre-registered results come from one run of `ai/evaluation/locked_eval.py --final`
> on the locked test with human labels and replace these tables: **To be filled**.

## 7.1 Protocol

Fixed before any human label ([prereg.md](../prereg.md)): metrics AURC (primary), AUROC for
catching unacceptable drafts, ECE, Brier, risk at 50/70/90% coverage; group-aware bootstrap
intervals (1,000 resamples). H1 to H3 decision rules are applied by code; one clarification
to H2 was logged before any locked-test access.

## 7.2 Proposed model versus baselines (H1, development)

| Method | AURC | 95% interval |
|---|---|---|
| Proposed | 0.134 | [0.072, 0.228] |
| B4 top-1 retrieval similarity (best baseline) | 0.174 | [0.113, 0.248] |
| B7 logistic regression on B4 to B6 | 0.180 | [0.107, 0.307] |
| B1 verbalised confidence | 0.197 | [0.130, 0.274] |
| B5 reranker score | 0.206 | [0.133, 0.291] |
| B6 entailment share | 0.216 | [0.129, 0.325] |
| B2 token probability | 0.261 | [0.158, 0.383] |

Paired difference against B4: −0.040 [−0.105, 0.038]: lower, but **no reliable
improvement** on 135 drafts. Figures: [risk-coverage](../results/figures/locked-rehearsal-judge/risk-coverage.svg),
[reliability](../results/figures/locked-rehearsal-judge/reliability.svg).

## 7.3 Risk control (H2, development)

Over 1,000 calibration/test resplits, Learn-then-Test certified a fast-lane threshold once:
**not testable** with judge labels. The assisted lane holds 86% of validation drafts at a
20.7% unacceptable rate; the escalate lane holds 14% at 47.4%.

## 7.4 Ablations

Dropping a feature group and measuring the change in validation AURC (positive = the group
helps; [ablations-v1-judge.json](../results/ablations-v1-judge.json)). Groups whose interval
excludes zero: category history (+0.109), routing (+0.070), cross-department probe
(+0.035), ticket (+0.017). Retrieval, reranker, grounding, consistency and evidence quality
did not reliably help on judge labels.

## 7.5 Unseen topics (H3) and the shift guard

Unseen-topic drafts are almost all unacceptable (0.7% acceptable), so AURC there is near 1
(0.992). On the three evaluation topics the guard cut unacceptable drafts shown from 75 to
25, at a cost of 4.35% of acceptable drafts on known topics
([shift-v1-judge.json](../results/shift-v1-judge.json)). Error analysis of what still gets
through: [error-analysis-v1-judge.md](../results/error-analysis-v1-judge.md).

## 7.6 Reproducibility

`python ai/evaluation/reproduce.py --offline` rebuilds every development table and figure
from a fresh clone without a database or GPU, byte for byte (Week 10 check).

## 7.7 User study (H4)

Design: 6 to 8 participants, within subject, manual versus workbench, two matched sets of
20 tickets, counterbalanced; handling time measured on the server, replies graded blind,
SUS after the workbench ([study kit](../study/user-study/README.md)). Analysis:
`python ai/study/analyse.py`. **To be filled** after the sessions.
