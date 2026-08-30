# Classification model

Week 4 note (Shivaganesh) on training and packaging the department/priority/sentiment
classifiers. Raw metrics live in the auto-generated
[classification-metrics.md](classification-metrics.md) (regenerated every time
`ai/models/train_classifier.py` runs); this doc explains what produced them and what
they actually mean.

## Training data

Two sources, combined:

- **Public dataset** (`data/processed/tickets_{train,val,test}.csv`, see
  [dataset-cleaning.md](dataset-cleaning.md)) — real ticket text, but only Networking
  and HR have any examples, and there's no sentiment field.
- **Synthetic tickets** (`data/synthetic_labeled_tickets.py`, 120 hand-authored
  examples, 24 per department) — covers all 5 departments and all 3 targets. Split
  70/15/15 stratified by department (same method as
  [split-strategy.md](split-strategy.md), seed 42) so it contributes to train/val/test
  in the same proportions, not just padded into training.

Department and priority train on the combined set (5,467 train / 1,172 test — the
public data dominates the row count). Sentiment trains on the synthetic split alone (84
train / 18 test), since the public dataset has nothing to contribute there.

## Method

Three independent `TfidfVectorizer` + `LogisticRegression(class_weight="balanced")`
pipelines — matching [architecture.md](architecture.md)'s "3 independent scikit-learn
pipelines, not one multi-output model" decision, since department/priority/sentiment
have unrelated label spaces. `class_weight="balanced"` because the department classes in
particular are extremely imbalanced (see below).

## Results, honestly read

- **Department: 93% accuracy, but 0.45 macro-F1.** The headline accuracy number is
  misleading on its own — it's driven almost entirely by Networking, which is 1,106 of
  1,172 test rows. SAP, Cloud, and Database each have only 3–4 test examples (all from
  the synthetic split) and correspondingly noisy per-class scores (Database: 0.00 F1).
  This isn't a bug in the classifier; it's a direct, honest consequence of the public
  dataset having zero real examples for those three departments — the same gap flagged
  in [dataset-cleaning.md](dataset-cleaning.md) since Week 2, now visible in a metric
  instead of just described.
- **Priority: 62% accuracy, 0.57 macro-F1.** More balanced classes (low/medium/high all
  have real support), so this number is more trustworthy than department's, but priority
  is intrinsically a harder signal from text alone — it depends on tone/urgency, not
  vocabulary, which TF-IDF captures only loosely. Usable as a first-pass signal, not
  something to route high-stakes decisions on without a human in the loop (which is the
  whole point of this project's confidence-gate design).
- **Sentiment: 72% accuracy, 0.71 macro-F1 — on only 18 test examples.** The number
  looks decent but the sample is small enough that it shouldn't be trusted much beyond
  "the pipeline works end-to-end." More synthetic examples (or a real sentiment-labeled
  source) would be needed before this number means much.

## What this means for Week 4 routing

The department classifier is good enough to demonstrate the pipeline — an End User
ticket does get classified and routed automatically — but its actual department
predictions for SAP/Cloud/Database should be expected to be unreliable given the
training data available. This is the correct place for that limitation to be visible
(a metrics table). It should not be read as "the routing feature doesn't work"; it
should be read as "the routing feature works, and the model behind it needs more real
per-department data before its predictions for the underrepresented departments can be
trusted."

## Packaging

`ai/models/classifier.py` loads the three saved pipelines
(`ai/models/artifacts/*.joblib`) once and exposes `classify_ticket(subject,
description) -> ClassificationResult(department, priority, sentiment)`. This is the
integration point Rishikesh's Week 4 pipeline work imports.

**The `.joblib` artifacts are committed to the repo** (unlike `data/raw/` and
`data/processed/`, which are gitignored) — they're small (~900KB total) and the live
pipeline needs them at runtime; requiring every checkout to retrain before the app
works would make the Week 4 "classified within a few seconds" demo unreliable. Re-run
`train_classifier.py` to regenerate them if the training data changes.
