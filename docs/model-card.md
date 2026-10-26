# Model card: TicketSense classifier and confidence model

Format after Mitchell et al., "Model Cards for Model Reporting" (Blueprint ref. [21]).
Owner: Shivaganesh. Status: **draft, development numbers** (validation split, LLM-judge
labels for the confidence model). Human-label and locked-test numbers: **To be filled**.

## 1. Department classifier

| Item | Value |
|---|---|
| Purpose | Route a support ticket to one of five departments: SAP, Cloud, Database, HR, Networking |
| Model | MiniLM sentence embeddings (`all-MiniLM-L6-v2`) plus TF-IDF features, logistic regression with balanced class weights (`ai/models/classifier_v2.py`) |
| Training data | Benchmark v1 train split (824 tickets) |
| Metrics | Macro-F1 0.911 on validation (known topics), 0.829 on unseen topics ([classifier-v2.json](results/classifier-v2.json)) |
| Also produces | Department probabilities and a cross-department probe, used by the confidence model and the shift guard |

## 2. Confidence model

| Item | Value |
|---|---|
| Purpose | Estimate the probability that an AI draft is acceptable (rubric A or M), to choose its lane |
| Version | `confidence-v1` |
| Model | XGBoost, chosen over logistic regression by validation AURC; Platt-calibrated on the calibration split (`ai/confidence_model/`) |
| Inputs | 31 signals of the draft (retrieval, reranker, grounding, consistency, routing, evidence, ticket) plus two category-history rates; no ticket text |
| Training labels | LLM judge (`llama3.1:8b`) for development; human labels for the reported model, **To be filled** |
| Output | A calibrated probability and up to three readable reasons |
| Thresholds | Learn-then-Test, α 0.10 (fast) and 0.40 (assisted), δ 0.10; with judge labels: fast not certified, assisted 0.05 with 100% coverage, so the score currently escalates no draft (calibrated scores range from 0.57 up; 21.1% of answering calibration drafts are unacceptable, under the 40% budget) |

### Development performance (validation, judge labels)

| Metric | Value |
|---|---|
| AURC | 0.134 [0.072, 0.228] |
| AUROC for unacceptable drafts | 0.695 |
| ECE | 0.106 |
| Brier | 0.174 |

Best single baseline: top-1 retrieval similarity, AURC 0.174 ([results draft](results-draft.md)).

## 3. Intended use

- Deciding whether an engineer sees an AI draft and how much checking it needs, in an
  internal IT and HR helpdesk whose knowledge base the system was built on.
- Always with a human making the final decision on every ticket.

## 4. Out-of-scope use

- Sending replies without human review.
- Tickets about topics the knowledge base does not cover: the score is unreliable there;
  the shift guard escalates such tickets but does not catch all of them.
- Any helpdesk other than the one whose knowledge base and history it was trained on.

## 5. Known failure modes

- **The score does not yet decide a lane.** With the current thresholds the assisted lane
  admits every draft that passes the can-answer flag, the output screen and the shift
  guard; a low-quality draft on a known topic is not held back by its score. The score
  only orders drafts and explains them until a fast-lane threshold can be certified.
- **Confidently wrong routing** on unseen topics: drafts from the wrong department can
  score high. The shift guard removed 50 of 75 such unacceptable drafts on evaluation
  topics; 25 still reached the assisted lane ([shift-v1-judge.json](results/shift-v1-judge.json)).
- **Category history dominates**: the model relies most on past acceptance rates of the
  department and topic, so a new or rare topic inherits the overall rate.
- **Fold sensitivity**: validation AURC moved from 0.149 to 0.134 when only the row order
  changed; small differences between models are not meaningful.
- **Judge labels**: the development model learns the LLM judge's view of acceptability,
  which agrees with a human on 82% of 28 pilot drafts.

## 6. Ethical considerations

- Trained only on synthetic tickets; no personal data. Personal data in live tickets is
  redacted before any model sees it.
- The fail-closed design escalates whenever the model, thresholds or screen are missing or
  uncertain, so a failure removes AI help rather than adding risk.

## 7. Caveats

All numbers here are development numbers. The reported model is trained on human labels and
evaluated once on the locked test.
