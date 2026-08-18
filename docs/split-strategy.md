# Train / validation / test split strategy

Week 2 note (Shivaganesh) defining the split strategy for the classification model,
per the project blueprint's Section 11.1 ("approximately 70% training, 15% validation,
and 15% held-out test, stratified by department"). Implemented in
`data/split_dataset.py`, run against `data/processed/tickets_clean.csv` (see
[dataset-cleaning.md](dataset-cleaning.md)).

## Strategy

- **70/15/15 train/validation/test**, split in two stages: 70/30 first, then the
  remaining 30% split evenly into validation and test (`sklearn.model_selection.
  train_test_split`, `test_size=0.30` then `test_size=0.50`).
- **Stratified by `department`** at both stages, so each split preserves the same class
  proportions as the full dataset — important given the imbalance documented in
  [dataset-cleaning.md](dataset-cleaning.md) (currently ~95% Networking, ~5% HR).
  Without stratification, a random split could plausibly leave the validation or test
  set with too few HR examples to evaluate that class meaningfully.
- **Fixed random seed (`42`)** so the split is reproducible across runs and across team
  members — anyone re-running `clean_dataset.py` + `split_dataset.py` gets the identical
  split, which matters once model comparisons depend on evaluating against the same test
  set.
- **Split at the ticket level, not by any grouping key.** There's no natural grouping
  (e.g. same customer, same underlying incident) evident in this dataset, so row-level
  stratified splitting is sufficient — revisit if a grouping key becomes relevant once
  resolved-ticket similarity data exists.

## Result (current data)

| Split | Rows | Networking | HR |
|---|---|---|---|
| train | 5,383 | 5,139 | 244 |
| val | 1,154 | 1,102 | 52 |
| test | 1,154 | 1,102 | 52 |

## What this doesn't solve yet

- **Only 2 of 5 departments have any rows to split.** This strategy splits whatever data
  exists; it doesn't manufacture SAP/Cloud/Database examples. Once synthetic
  department-labeled tickets exist (see `dataset-cleaning.md`'s known limitations), they
  need to go through the same stratified split, not be added only to `train`.
- **Class imbalance survives the split** (proportional by design) — the classifier
  training step (not started) will need to handle this explicitly (class weights,
  oversampling, or evaluating with macro-averaged metrics rather than accuracy), not
  something the split alone fixes.
- **No split yet for `priority` or `sentiment` as classification targets.** This split is
  keyed on `department` only, matching `docs/architecture.md`'s note that the three
  classifiers are independent pipelines with unrelated label spaces — priority and
  sentiment splits (once sentiment labels exist) may need their own stratification key
  rather than reusing this exact split.
