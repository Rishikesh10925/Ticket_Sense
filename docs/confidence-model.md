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

## Week 9 refinement: real feedback enters the training set

The confidence gate went live this week (`ai/graph/nodes.py::gate_condition`,
[langgraph-pipeline.md](langgraph-pipeline.md)), and the reviewer UI
(`frontend/src/components/ReviewActions.tsx`) started actually populating the
`feedback` table. `ai/confidence/labels.py` implements the accept/edit/reject/escalate
→ success/failure mapping [confidence-labelling-guide.md](confidence-labelling-guide.md)
proposed back in Week 3 as a plan, including its explicit "minor vs. heavy edit"
open question — resolved for now with the guide's own recommended starting point
(difflib's edit-distance ratio, <15% changed = minor), and its note that a reviewer
escalating a ticket that already had a draft should be labelled like a reject.

`ai/confidence/train.py` now builds two datasets and combines them: every real
(non-synthetic-reviewer) `feedback` row, labeled via `labels.py` using the exact
`confidence_features` already stored on the ticket at scoring time; plus the Week 8
synthetic-bootstrap fallback for any ticket that doesn't have a real label yet. **Real
labels always win** — a synthetic label is only used when no real one exists for that
ticket — implementing this week's "real outcomes as the primary training signal going
forward" ask as an actual precedence rule in the training code, not just a stated
intention.

### What "real" means today, honestly

As of this write-up, the only non-synthetic `feedback` rows in the database are four
QA actions taken while verifying the Week 9 reviewer UI end-to-end in a live
browser — one Accept, one Edit, one Reject, and one reviewer-initiated Escalate, one of
each so every code path got exercised. **These are not organic reviewer judgments
about draft quality.** The Reject reason and the Edit's replacement text were both
written to exercise the API contract (a non-empty `reject_reason`/`edited_reply`), not
to record a real opinion about whether that specific draft was good. Retraining on them
proves the mechanism — real rows really do get queried, really do get labeled, really
do enter the dataset ahead of synthetic ones — but says nothing about actual model
quality yet, the same way Week 8's synthetic labels proved the pipeline without proving
calibration.

Retrained result: **99 train / 25 test (4 real, 120 synthetic), accuracy 0.44,
ROC-AUC 0.571** — see [confidence-metrics.md](confidence-metrics.md) for the full
table. This is *worse* than Week 8's 0.54/0.605, and that's reported plainly rather
than smoothed over: four labels cannot meaningfully shift a 124-example dataset's
signal, and the honest read is that this run's number is mostly sampling noise from a
different train/test split, not evidence the model got worse. The number that matters
this week isn't the metric, it's that the real-label pathway now works and is wired to
prefer real data as it accumulates.

One structural check the four QA rows did validate: the Edit case (a 754-character
draft fully replaced by a 94-character QA note) correctly computed a >85% change ratio
and was labeled a failure — confirming `label_from_feedback`'s minor/heavy distinction
fires correctly on a real edit, not just on the unit tests in
`backend/tests/test_confidence_labels.py`.

## First real gate decisions: what can (and can't) be said yet

Week 9's roadmap asks for an early look at real gate decisions for obviously
miscalibrated cases. Honest answer: **not yet possible.** The only tickets that have
gone through the live gate with a real reviewer's follow-up are the same four QA
tickets above, and since those reviewer actions were chosen to exercise each button
rather than to judge draft quality, their outcomes (3 of 4 labeled "failure" despite
all four scoring 0.78–0.79, comfortably above Networking's 0.45 threshold) reflect the
test design, not the model. Reading that 3:1 ratio as "the gate is miscalibrated"
would repeat the exact mistake this project has avoided since Week 1 — treating
placeholder data as if it were real evidence. A genuine miscalibration analysis needs
organic reviewer usage: real engineers reviewing real drafts because they need the
ticket resolved, not because someone is testing the Accept button. That's Week 10+
territory once the system has actual traffic.

## What's next

- Real Accept/Edit/Reject/Escalate outcomes need organic volume — dozens, not four —
  before a retraining pass or a miscalibration review says anything trustworthy.
- `document_freshness`/`ocr_confidence` still need real variance in the training
  set — none of the four real rows so far involve an attachment or a wide time spread,
  so this Week 8 limitation is unchanged.
- Once organic real-feedback volume exists, revisit the minor/heavy edit-distance
  threshold (currently 0.15, unvalidated) against a manual spot-check, per the
  labelling guide's own open question.
