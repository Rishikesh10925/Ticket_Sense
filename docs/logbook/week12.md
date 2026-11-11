# Logbook — Week 12 (4 to 10 Jan 2027): final integration and evaluation ★ milestone

## Exit gate

| Condition | Status | Evidence |
|---|---|---|
| Locked test evaluated exactly once | **green** | [locked-final-judge.md](../results/locked-final-judge.md); access log records one final read (2026-11-11 11:36 UTC) |
| Human evaluation | **amber** | Three-author audit: batch 1 rated and collected, adjudication in progress, batch 2 to do |
| Final report | **amber** | Report chapters drafted; experiments chapter has the locked-test result |
| Fresh checkout runs; tagged release | **pending** | Fresh-setup timing and the `v1.0` tag after the author audit |
| Demo rehearsal, slides, user study | **pending (human)** | Storyboard ready ([demo/storyboard.md](../demo/storyboard.md)); study tool ready |

## Protocol changes (all logged before the data they affect)
- **2026-11-02:** outside-reviewer audit of 40 frozen validation and unseen-topic drafts.
  Its 80 ratings are kept as an exploratory pilot (poor agreement, signs of pasted reasons).
- **2026-11-03:** the 600-draft labelling was cancelled; the human evaluation is the
  three-author audit (rubric AUTHOR-v2, [author-audit/](../author-audit/README.md)).
- **2026-11-11:** the locked test is run once against LLM-judge labels (prereg amendment).

## Locked-test result (271 drafts, judge labels)

| Hypothesis | Decision |
|---|---|
| H1 | **No reliable improvement.** AURC 0.352 vs 0.398 (B4); difference −0.045 [−0.136, 0.066] |
| H2 | **Not testable.** No fast threshold certified in 999 of 1,000 resplits |
| H3 | Seen AURC 0.352 [0.263, 0.452]; unseen 0.992 (2 of 283 acceptable). The guard cuts unseen drafts shown from 152 to 58 |

## Three-author audit, batch 1 (20 drafts, original ratings)
- Agreement is low: Krippendorff's alpha 0.21 [−0.09, 0.48] on acceptable vs not; 0.05 on
  the four-way grade and on citation support; −0.10 on relevance.
- No case is unanimously "grounded but unacceptable". 48 disputed questions go to the
  joint adjudication session.

## Rishikesh
- Outside-reviewer pages and collection with timing and pasted-reason checks.
- Three-author audit: frozen plan, pages in two batches, Krippendorff's alpha, adjudication page.

## Aashritha
- Batch 1 ratings (AUTH-A).

## Shivaganesh
- Batch 1 ratings (AUTH-S); prereg amendment and the one locked-test run.

## Findings
- **Held out, the model is no better than its best single signal.** The direction matches
  validation, but the interval crosses zero.
- **The judge is not a stand-in for people.** Humans agree poorly even with each other on
  these drafts, so judge-labelled numbers are reported with that limitation.
