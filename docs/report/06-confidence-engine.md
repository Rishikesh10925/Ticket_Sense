# 6. The confidence engine and risk control

*Owner: Shivaganesh. Draft v1. Code: `ai/confidence_model/`, `ai/evaluation/risk_control.py`, `ai/gate/`.*

## 6.1 Signals

31 features per draft in seven groups (retrieval, reranker, grounding, consistency,
routing, evidence quality, ticket), plus two category-history features (smoothed past
acceptance rates of the department and topic, learned from training labels only).

## 6.2 Model

Two candidates, chosen by validation AURC: logistic regression (median imputation with
missing-value flags) and XGBoost (native missing values, one thread for reproducibility).
Hyperparameters by group-aware five-fold cross-validation on the train split. Scores are
calibrated with Platt scaling on the calibration split; isotonic regression was tried
first and rejected because its ties raised validation AURC.

For each draft the model also returns readable reasons: the signals that pulled its score
down most (for example "low reranker score", "another department matches as well").

## 6.3 Thresholds

Learn-then-Test on the calibration split over a grid fixed in advance (0.99, then 0.95 down
to 0.05): fast lane α = 0.10, assisted lane α = 0.40, δ = 0.10. With judge labels no fast
threshold can be certified; the assisted threshold is 0.05. The fast lane therefore stays
closed until human-label calibration certifies one.

### What the assisted threshold does today: nothing

The assisted threshold was certified at **0.05, the lowest point of the grid, with 100%
coverage** of the 232 calibration drafts that can answer (thresholds are certified on
those, since a draft that cannot answer always escalates). Two facts make that the outcome:

- **The budget is looser than the base rate.** Only 21.1% of the answering calibration
  drafts are unacceptable (49 of 232), below the 40% assisted budget, so even "show every
  draft" passes the test. The same holds for any budget of 30% or more. At 25% a threshold
  of 0.65 is certified (94% coverage); at 20% or less none can be, because the fixed
  sequence fails before reaching a useful one (`alpha_curve` in `confidence-v1-judge.json`).
- **The calibrated scores never come near 0.05.** The lowest score the model gives is
  0.57 on calibration, 0.62 on validation and 0.63 on unseen topics.

So **no known-topic draft is escalated because of its confidence score.** In the live
gate a draft reaches the assisted lane unless one of three other checks stops it:

| Check | What escalates | Validation, judge labels |
|---|---|---|
| Can-answer flag | The drafting model said the evidence cannot answer | 19 of 135 drafts |
| Output screen | A step contains a URL, command or code its evidence does not | blocked drafts are never shown |
| Shift guard | Routing looks unlike the calibration data (department probability below 0.5, or another department within 0.1) | flags 27 of 135 |

The confidence score still matters in three ways: it orders the queue, its reasons are
shown to the engineer, and it is what the fast lane will use once a threshold can be
certified. But until then **the gate's protection comes from the can-answer flag, the
output screen and the shift guard, not from the score.** Whether human labels change this
(a different unacceptable rate, a different score range) is part of the locked evaluation.

## 6.4 Shift guard

Thresholds certified on known topics do not hold on unseen ones. The guard escalates a
draft when the classifier's top department probability is below 0.5 or another department
matches within 0.1. It was chosen on three withheld topics and evaluated on three others
(Chapter 7).

## 6.5 Lanes in the product

The gate runs live for every ticket; the lane is stored on the ticket, badged in the
engineer queue and explained on the ticket page. The admin can see the active, versioned
thresholds and a lane dashboard (mix, acceptance per lane, decision time).
