# Pre-registration

- Status: **v1, tagged `prereg-v1` on 2026-10-19 (Week 3)**, before any
  human labels are collected. After the tag, this file changes only through the
  amendment log at the bottom.
- Owner: Shivaganesh. Source: Blueprint V2 §6, §14, §15.

## Research questions

| ID | Question | Owner |
|---|---|---|
| RQ1 | Does an independently trained confidence model rank AI drafts by correctness better than the strongest single signals (verbalised confidence, token probability, self-consistency, top-1 retrieval similarity, entailment score)? | S |
| RQ2 | Can a statistical threshold-selection step hold the fast-lane error rate under a chosen budget on unseen tickets? | S |
| RQ3 | How do retrieval and grounding quality limit draft quality, and how does the gate behave on unanswerable tickets and unseen topics? | R |
| RQ4 | Does the lane design reduce an engineer's handling time without increasing accepted errors? | A |

## Outcome variable

Binary `acceptable` from the [labelling rubric](labelling-rubric.md): labels A or M are 1,
labels R or W are 0. Headline numbers use **human labels only**. LLM-judge labels supply
training volume and are reported with their agreement against humans.

## Data and splits

Benchmark v1, frozen 2026-10-19 ([FREEZE_v1.json](../data/benchmark/FREEZE_v1.json), tickets
SHA-256 recorded there): 1,775 tickets from 596 scenarios, of types A 975 (54.9%), B 265
(14.9%), C1 unseen topic 355 (20.0%), C2 out of domain or vague 180 (10.1%). Splits are
grouped by gold article (leakage unit): train 824, validation 135, calibration 262 (200
human-labelled), locked test 271 (250 human-labelled, stratified), and unseen 283 (all C1).
Every evaluation run first checks `freeze.py verify`. The locked test set is read only
through `ai/evaluation`, exactly once, in Week 10.

## Methods compared

B0 always-show / always-escalate · B1 verbalised confidence · B2 token log-probability
(conditional on provider support) · B3 self-consistency · B4 top-1 retrieval similarity ·
B5 cross-encoder score · B6 entailment share · B7 logistic regression on B4+B5+B6 ·
**Proposed**: full feature model, calibrated, with risk-controlled thresholds.

## Hypotheses and decision rules

| ID | Hypothesis | Decision rule |
|---|---|---|
| H1 | The confidence model has lower AURC than the best baseline. | "Best baseline" = lowest validation AURC among B1 to B7, fixed before the locked test. Supported if the paired bootstrap 95% interval (1,000 group-aware resamples) of AURC(proposed) − AURC(best baseline) on the locked test lies entirely below zero. Otherwise report "no reliable improvement". |
| H2 | The risk-controlled fast lane keeps the unacceptable-draft rate at or below α. | α = 0.10, δ = 0.10. Over 1,000 random calibration/test resplits of the human-labelled pool, the test-side fast-lane risk is ≤ α in at least 90% of splits. |
| H3 | Performance degrades on unseen topics. | Report AURC and fast-lane risk for seen vs unseen topics with 95% intervals. Degradation is an expected finding, not a failure. |
| H4 | The AI-assisted workflow cuts median handling time by at least 20% with no increase in accepted major errors. | Paired within-subject comparison, reported descriptively with a small-sample caveat. |

## Secondary metrics

AUROC for detecting unacceptable drafts, ECE (10 equal-width bins), Brier score, risk at
50/70/90% coverage, per-lane coverage, the share of unacceptable drafts caught before the
fast lane, and the false-escalation rate. Slices: ticket type, department, seen/unseen.

## What will not be done

- No tuning, model selection or threshold choice on the locked test set.
- No re-running the locked evaluation after seeing results; any later change is a new,
  separately reported evaluation.
- No dropping of baselines or slices that turn out unfavourable.

## Amendment log

| Date | Change | Reason |
|---|---|---|
| 2026-10-19 | Tagged `prereg-v1` with the frozen counts above (1,775 rather than about 1,800 tickets; test 271 and calibration 262 rather than 250). | Exact numbers from the freeze; 28 paraphrases failed generation quality checks and were dropped. |

| 2026-10-20 | KB amendment 1 (`data/benchmark/FREEZE_v1_amend1.json`): SAP-PO-002, SAP-PO-004 and SAP-MAT-002 steps and key facts corrected after an AI-assisted fact-check of the 24 SAP articles. Tickets and splits unchanged. Drafts that cited these articles are regenerated with the corrected text before any human label is collected on them. | Factual errors found in the knowledge base. The 24 SAP articles are recorded as `reviewer: Claude` (AI-checked); this is not the blueprint's human second-member review, which remains outstanding for all 120 articles. |
| 2026-10-21 | H2 clarification, made before the locked test was read: a resplit in which Learn-then-Test certifies no fast-lane threshold shows nothing on the test side and is counted as within α, as the rule says; but if that happens in more than half of the 1,000 resplits, H2 is reported as **not testable** rather than supported. ECE and Brier are reported only for scores meant as probabilities (proposed, B1, B2, B7). | The Week 10 rehearsal on validation (judge labels) closed the fast lane in all 1,000 resplits, which would have made H2 "supported" without the lane ever showing a draft. |
| 2026-10-25 | H3 additions, made before the locked test was read: alongside the pre-registered AURC and fast-lane risk, report the number of acceptable and unacceptable drafts, e-AURC with its interval (marked not informative when either class has fewer than 10 drafts), and exposure: drafts shown and unacceptable drafts shown, with and without the shift guard. Nothing pre-registered is dropped or changed. | In the Week 10 rehearsal only 2 of 283 unseen-topic drafts were acceptable, so unseen AURC (0.992) reflects the base rate, not the ranking; how many bad drafts reach an engineer is the meaningful quantity. |
| 2026-10-25 | B3 self-consistency added to the locked evaluation, where it had been left out by mistake. A draft with no claims (it cannot answer, or failed the schema) has no B3 and scores 0, like any missing signal. B3 is a candidate for "best baseline" (H1) only if it covers at least 95% of the answering validation drafts; its coverage is reported, and the proposed model is also compared with B3 on the drafts that have it (descriptive). | The pre-registration lists B1 to B7, but the runner compared only B1, B2 and B4 to B7. B3 needs k re-drafts per ticket, so it was computed only for the drafts selected for labelling: it covers every answering selected draft (313 of 313 outside the locked test), but only 16% of answering drafts on the judge-labelled validation split. |
| 2026-10-26 | H2 procedure made to match the deployed gate, before the locked test was read: in each of the 1,000 resplits, Platt calibration is refitted on the calibration side only (from uncalibrated scores), the fast threshold is certified on that side's drafts that can answer, and the risk is measured on the test side's drafts that can answer. The production thresholds (`train.py`) are likewise certified on answering calibration drafts. The rule (risk ≤ α in at least 90% of resplits; not testable if the lane never opens in most) is unchanged. | Review found that H2 scored the whole pool with a calibrator fitted on its calibration rows, so test-side drafts could have shaped their own scores, and counted drafts that cannot answer as shown although the live gate always escalates them. |

Standing rule: if the human fact-check of the KB changes an article, the tickets written
from it are regenerated, the benchmark is refrozen as v1.1, and the change is logged
here *before* any human label is collected on the affected tickets.
