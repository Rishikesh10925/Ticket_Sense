# Results (draft)

- Owner: Shivaganesh. Roadmap Week 10: "write the Results draft"; logbook: "evaluation
  record and limitations list".
- Status: **draft before the locked test**. Every number below is a development number,
  from the validation split with LLM-judge labels (`--rehearse`). The pre-registered
  results come from one run of `ai/evaluation/locked_eval.py --final` on the locked test
  with human labels. That run replaces every table here and is reported whatever it shows
  ([prereg.md](prereg.md)).

## How the numbers are produced

```bash
python ai/evaluation/reproduce.py              # every development table and figure
python ai/evaluation/reproduce.py --offline    # the same from a fresh clone, no database or GPU
python ai/evaluation/locked_eval.py --final --confirm "run the locked test once"   # once, after human labels
```

A fresh clone with a clean virtual environment reproduces every committed table and figure
byte for byte from `data/eval/eval_inputs_v1.jsonl.gz` (Week 10 check). The export
leaves out the locked test.

## Evaluation record

| Item | State on 2026-10-21 |
|---|---|
| Benchmark freeze and locked-test seal | verified on every run |
| Locked test read | **never**: `data/annotation/locked_test_access.log` does not exist |
| Human labels collected | 0 of the 600 selected drafts (250 locked test, 200 calibration, 150 train and validation) |
| Best baseline for H1 | chosen from the validation table before the final run; with judge labels it is B4 (top-1 similarity) |
| Rule changes | one clarification, logged in the prereg amendment log on 2026-10-21 before any test access: H2 is "not testable" if the fast lane opens in fewer than half of the resplits |

## Development numbers (validation, judge labels: not results)

Validation: 135 drafts, 75.6% acceptable by the judge.

| Method | AURC | 95% interval | AUROC (unacceptable) | ECE | Brier |
|---|---|---|---|---|---|
| Proposed (XGBoost, Platt-calibrated) | 0.134 | [0.072, 0.228] | 0.695 | 0.106 | 0.174 |
| B1 verbalised confidence | 0.197 | [0.130, 0.274] | 0.622 | 0.177 | 0.210 |
| B2 token probability | 0.261 | [0.158, 0.383] | 0.459 | 0.084 | 0.197 |
| B4 top-1 retrieval similarity | 0.174 | [0.113, 0.248] | 0.644 | n/a | n/a |
| B5 reranker score | 0.206 | [0.133, 0.291] | 0.628 | n/a | n/a |
| B6 entailment share | 0.216 | [0.129, 0.325] | 0.545 | n/a | n/a |
| B7 logistic regression on B4 to B6 | 0.180 | [0.107, 0.307] | 0.625 | 0.060 | 0.174 |

ECE and Brier are only meaningful for scores meant as probabilities. B3 (self-consistency)
was computed on a subset only and is reported in `baselines-v1-judge.json`.

| Hypothesis | Rehearsal outcome | What it would mean |
|---|---|---|
| H1 | AURC difference vs B4: -0.040 [-0.105, 0.038], **no reliable improvement** | The interval crosses zero on 135 drafts. The locked test (250) may or may not separate them. |
| H2 | **not testable**: the fast lane opened in 1 of 1,000 resplits | With judge labels no threshold is certifiable at a 10% error budget; the fast lane stays closed. |
| H3 | seen AURC 0.134 [0.072, 0.228]; unseen 0.992 [0.979, 1.000] | Unseen-topic drafts are almost all unacceptable (0.7% acceptable), so their AURC is near 1 by construction. The shift guard (Week 9) is the response. |

Lanes on validation: fast 0%, assisted 86%, escalate 14%. 9.8% of acceptable drafts
are escalated (false escalations).

Figures: [`figures/locked-rehearsal-judge/`](results/figures/locked-rehearsal-judge/)
(risk-coverage, reliability, H2 resplits).

## Other results already measured

- Red team through the full pipeline: 0 of 40 injection tickets reach an engineer
  ([redteam-v3-pipeline.json](results/redteam-v3-pipeline.json)).
- Latency: median 6.4 s per ticket, of which the gate is 6 ms ([latency-cost.md](latency-cost.md)).
- Judge versus one team member on the 28 pilot drafts with both labels: binary agreement 82%,
  kappa 0.58 ([agreement-v1.json](results/agreement-v1.json)). Agreement among
  reviewers is not measured yet.

## Limitations (to keep in the final report)

1. **No human labels yet.** Every number above uses the LLM judge, whose agreement with
   humans is measured on 28 drafts and one member only.
2. **Synthetic benchmark.** Tickets are generated paraphrases of KB scenarios (1,775
   tickets from 596 scenarios), not real helpdesk traffic.
3. **Fold sensitivity.** Fixing only the row order the model sees changed the
   validation AURC from 0.149 to 0.134 (Week 10). Single-split numbers carry that much
   noise on top of the bootstrap interval.
4. **The fast lane is closed, and the assisted threshold filters nothing.** No threshold
   could be certified at the 10% budget, so the design runs as two lanes. The assisted
   threshold was certified at 0.05 with 100% coverage: only 22.5% of calibration drafts
   are unacceptable (below the 40% budget) and no calibrated score is below 0.57. Known-
   topic drafts are therefore escalated by the can-answer flag, the output screen and the
   shift guard, not by their confidence score (report Chapter 6.3).
5. **Unseen topics.** Almost every unseen-topic draft is unacceptable; the shift guard
   reduces how many reach an engineer but was tuned and evaluated on three topics each.
6. **Output screen trade-off.** Screen v2 blocks 87 of 1,484 shown drafts on the full
   benchmark, including 47 the judge rated acceptable that contain commands not in the
   cited evidence. Kept on purpose for safety.
7. **Knowledge base review.** The 24 SAP articles were fact-checked by an AI, not by a
   second team member; the human review of all 120 articles is outstanding.
8. **One machine.** Latency was measured on one laptop, one ticket at a time.

## To be filled from the final run

- The tables above, on the locked test with human labels.
- H1 to H3 decisions, recorded exactly as the rules produce them.
- A second member reproduces the headline numbers (Week 10 exit gate).
