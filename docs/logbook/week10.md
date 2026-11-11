# Logbook — Week 10 (21 to 27 Dec 2026): analytics and evaluation ★ milestone

## Exit gate

| Condition | Status | Evidence |
|---|---|---|
| Analytics dashboard live | **green** | Dashboard v1: lane mix, acceptance, latency, gate confidence |
| Full evaluation suite computed and compared with the baselines | **green (rehearsal)** | [locked-rehearsal-judge.md](../results/locked-rehearsal-judge.md), validation split, judge labels |
| Integration test pass | **green** | [usability-pass-week10.md](../study/usability-pass-week10.md); every evaluation command smoke-tested on synthetic rows |
| Fresh clone reproduces the results | **green** | `python ai/evaluation/reproduce.py --offline` rebuilds the committed tables byte for byte |

## Results (rehearsal: validation split, judge labels; not the locked test)

| Hypothesis | Decision |
|---|---|
| H1 | No reliable improvement: AURC difference vs B4 −0.040 [−0.105, 0.038] |
| H2 | Not testable: the fast lane never opens |
| H3 | Seen AURC 0.134, unseen 0.992 (only 2 of 283 unseen drafts acceptable) |

Latency ([latency-cost.md](../latency-cost.md)): median 6.4 s per ticket, of which drafting
is 88%; the confidence gate adds a median 5.6 ms.

## Rishikesh
- Evaluation inputs exported without the locked test; `reproduce --offline` with no database or GPU.
- Rows loaded in one fixed order (the database and the export gave different tables before).
- CI enforces 70% coverage on the evaluation and pipeline packages; latency v2 and the latency and cost report.

## Aashritha
- Dashboard v1; keyboard and label fixes from the usability and accessibility pass; demo storyboard.

## Shivaganesh
- Locked-test runner with a validation rehearsal and SVG figures; prereg clarification that
  H2 is "not testable" when the fast lane never opens; results chapter draft.

## Findings
- **Row order changed the numbers.** Same rows in another order gave different XGBoost
  folds; fixing the order moved validation AURC from 0.149 to 0.134.
