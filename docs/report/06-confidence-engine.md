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

## 6.4 Shift guard

Thresholds certified on known topics do not hold on unseen ones. The guard escalates a
draft when the classifier's top department probability is below 0.5 or another department
matches within 0.1. It was chosen on three withheld topics and evaluated on three others
(Chapter 7).

## 6.5 Lanes in the product

The gate runs live for every ticket; the lane is stored on the ticket, badged in the
engineer queue and explained on the ticket page. The admin can see the active, versioned
thresholds and a lane dashboard (mix, acceptance per lane, decision time).
