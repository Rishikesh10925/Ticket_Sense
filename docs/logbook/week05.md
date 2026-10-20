# Logbook — Week 5 (16 to 22 Nov 2026): cited drafts and claim checking

## Exit gate

| Condition | Status | Evidence |
|---|---|---|
| At least 95% of drafts validate against the schema | green | **1,773 / 1,775 (99.9%)**, prompt `draft-v2`, all benchmark tickets |
| NLI scorer runs over the full benchmark offline | green | Claims checked for every shown draft (`draft_claims`) |
| Audit sample chosen | green | `docs/audit/audit_sample_v1.json`: 100 drafts, 495 claims, stratified by type and support band; worksheets per member |
| Team pilot of 30 drafts | **pending (humans)** | `docs/pilot/pilot_v1.csv` ready |

## Results on benchmark v1 (all 1,775 tickets)

| Type | Drafts | Schema-valid | Model answered | Mean groundedness | Judge: acceptable | Judge labels A / M / R / W |
|---|---|---|---|---|---|---|
| A | 975 | 99.8% | 97.6% | 0.670 | 75.3% | 0 / 734 / 222 / 19 |
| B | 265 | 100% | 96.6% | 0.632 | 85.7% | 0 / 227 / 27 / 11 |
| C1 | 355 | 100% | **54.4%** | **0.402** | **0.6%** | 0 / 2 / 0 / 353 |
| C2 | 180 | 100% | 42.8% | 0.624 | 60.0% | 0 / 108 / 15 / 57 |

Judge: `llama3.1:8b`, prompt `judge-v0`. These are **judge** labels (training volume
only), not the human labels the headline numbers will use.

## Rishikesh
- LangGraph flow complete: extract → redact → classify → route → retrieve → draft → check → signals → score → gate. Every draft and its claims persisted; `GET /tickets/{id}/draft`.
- `draft-v2`: the JSON schema now requires at least one citation per step. `draft-v1` lost 6% of drafts (11 of the first 180) to "step without citation"; with constrained decoding the model can no longer emit an uncited step. Schema-valid went from 93.9% to 99.9%.
- Batch speed: the drafting model now stays fully on the GPU while the NLI checker runs beside it in half precision (`ai/devices.py`). 6.2 drafts a minute, up from about 3; the full benchmark drafted in 3 hours.

## Aashritha
- Draft panel: cited steps, side-by-side evidence, unsupported claims highlighted, loading/empty/error states, lane placeholder. Verified in a browser with the real model.
- Reviewer guide and training plan; pilot worksheet.

## Shivaganesh
- NLI claim checker and self-consistency sampler; verbatim-quote rule after the checker scored an exact copy of the evidence at 0.003.
- Batch drafting and batch judging (both resumable, cached); audit sample selection.

## Findings
- **Unseen topics are the hard case, as designed.** On C1 tickets the model still answers 54% of the time although it never saw the article, and the judge rejects nearly all of those. Groundedness already separates them (0.40 against 0.67 on A). Catching these is the confidence gate's job.
- **The judge never awards A** (send as is), only M at best. It is strict, not wrong on the binary target, but it is one more reason headline numbers use human labels, and the judge will be calibrated against the 60 pilot labels in Week 6.
- **B tickets score higher with the judge than A** (85.7% against 75.3%). The judge may be lenient on the unanswerable extra question; the pilot and the human labels will tell.

## Open items for the team (humans)
- Label the 30 pilot drafts (about an hour each), then meet to settle disagreements.
- Run the 100-draft groundedness audit (`docs/audit/`, about 1.5 to 2 hours each).
- Fact-check the 120 articles; recruit reviewers; mentor sign-off.
