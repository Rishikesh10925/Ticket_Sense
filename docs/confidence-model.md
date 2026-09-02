# Confidence model

Week 8 note (Shivaganesh) on the first version of the independent confidence
classifier — `ai/confidence/` — that will decide (Week 9) whether a generated draft
is reliable enough to reach a human reviewer, or whether the ticket should be
escalated untouched. See [architecture.md](architecture.md) for why this is a
separately trained model and not the LLM's own self-assessment.

## Feature set

Five features, computed in `ai/confidence/features.py` from data already available at
draft time — nothing here asks the LLM anything about itself:

| Feature | What it measures | Source |
|---|---|---|
| `retrieval_relevance` | Average similarity (`1 - cosine_distance`) of the retrieved evidence | `ai/embeddings/retrieve.py`'s `EvidenceResult.distance` |
| `ticket_resolution_similarity` | Similarity of the closest matching **resolved ticket**, specifically | Same evidence, filtered to `source_type == "resolved_ticket"` |
| `document_freshness` | How recently the retrieved evidence was updated, averaged, with a 180-day half-life decay | `EvidenceResult.updated_at` (added this week — KB articles and resolved tickets both already had `updated_at`, retrieval just didn't select it before) |
| `ocr_confidence` | The Week 7 OCR/extraction confidence, or `1.0` if the ticket has no attachment | `Ticket.ocr_confidence` |
| `category_risk` | `1 - (department classifier's macro-avg F1 for the routed department)` | [classification-metrics.md](classification-metrics.md) |

`category_risk` is the one feature worth explaining: it isn't a guess. It's directly
derived from the department classifier's own measured, already-published accuracy per
department (Networking 0.96 F1 → risk 0.04; Database 0.00 F1 → risk 1.00). The
reasoning: if the classifier is unreliable for a department, then "is this ticket even
in the right queue" is itself uncertain, and that uncertainty should push the
confidence score down regardless of how good the retrieved evidence looks — a
low-relevance-error can be caught by a human, but a wrong-department error means the
evidence itself was searched in the wrong place.

## What the synthetic labels are (and aren't)

No real human review outcomes exist yet — Week 9 is when the review UI starts
producing them (see [confidence-labelling-guide.md](confidence-labelling-guide.md)).
Training a first model without waiting for that meant bootstrapping labels somehow, so
`ai/confidence/synthetic_labels.py` defines an explicit, documented formula: a weighted
sum of the same five features, passed through a sigmoid, sampled with a fixed random
seed. The weights (retrieval relevance and category risk dominate; freshness and OCR
contribute less) are **a judgment call about what should plausibly matter, not fitted
to any real data.**

**This is honestly a proxy, not ground truth.** The model evaluated below is measuring
whether it can recover the synthetic formula's own logic from noisy, sampled labels —
that's a real and useful thing to verify (it proves the training pipeline, feature
computation, and evaluation code all work correctly end to end), but it says nothing
yet about whether the model will agree with what a real engineer actually does with a
real draft. Retraining on real Accept/Edit/Reject outcomes, starting Week 9, is what
turns this from "does the pipeline work" into "is this actually predicting anything
real."

## Training data

`ai/confidence/train.py` builds its dataset by running the **real** retrieval pipeline
against the 120 synthetic historical tickets already seeded in the database — each
ticket's own subject+description is the query, against its own already-correct
department, exactly like a live ticket would be scored. Only the label is synthetic;
every feature value is a real number computed from real retrieval against the real
`embeddings` table (with each ticket's own embedding excluded from its own results, so
it can't trivially match itself).

## Initial evaluation

96 train / 24 test (80/20 split, stratified, seed 42). Full table:
[confidence-metrics.md](confidence-metrics.md).

- **Accuracy: 0.54. ROC-AUC: 0.605.** Better than the 0.50 random baseline, but weak —
  an honest first result, not a strong one. With only 96 training examples and labels
  that are themselves noisy samples (not deterministic), this is roughly the ceiling of
  what to expect; it confirms the pipeline recovers *some* signal, not that the model
  is well-calibrated yet.
- **`category_risk`'s learned coefficient is −2.27, by far the largest in magnitude** —
  the model picked up on the same signal the synthetic formula weighted most heavily,
  a sign the training actually worked rather than fitting noise.
- **`document_freshness` and `ocr_confidence` both learned a coefficient of exactly
  0.000.** This is a real, honest limitation of the bootstrap dataset, not a modeling
  bug: none of the 120 synthetic historical tickets have an attachment, so
  `ocr_confidence` is `1.0` for every single training example — zero variance, nothing
  for the model to learn from. `document_freshness` has only slightly more variance
  (all 120 tickets were embedded within the same short window). Both features are
  correctly *implemented* (see `features.py`) but currently untested by this training
  run; real ticket traffic with real attachment timing will be needed before either
  feature's weight means anything.

## What's next

- Week 9 wires this model's score into the LangGraph pipeline's gate (`score` node →
  confidence-gate conditional edge).
- Real Accept/Edit/Reject/Escalate outcomes (Week 9+) replace the synthetic labels for
  every retraining pass after this one.
- `document_freshness`/`ocr_confidence` need real variance in the training set — likely
  from real submitted tickets rather than the synthetic historical set — before their
  weights can be trusted.
