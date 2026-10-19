# Pre-registration

- Status: **DRAFT v0 (Week 1)**. Committed and tagged `prereg-v1` in Week 3, before any
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

Benchmark v1 (frozen and hashed in Week 3): about 1,800 tickets of types A (55%), B (15%),
C1 unseen topic (20%), C2 out of domain or vague (10%). Splits are grouped by scenario:
train about 900, validation 150, calibration 250 (200 human-labelled), locked test 250
(all human-labelled), and an unseen-topic set (all C1). The locked test set is read only
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
| — | — | — |
