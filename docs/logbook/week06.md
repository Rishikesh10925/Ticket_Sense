# Logbook — Week 6 (23 to 29 Nov 2026): pipeline complete and the hard gate ★ M3

## Gate review (Roadmap: all four green, or a written recovery plan agreed with the mentor)

| Condition | Status | Evidence |
|---|---|---|
| Recall@5 ≥ 0.80 on type A | **green** | 1.000 (`docs/results/retrieval-v1.json`) |
| Schema-valid drafts ≥ 95% | **green** | 1,773 / 1,775 = 99.9% (`draft-v2`) |
| Audit agreement understood and acceptable | **amber** | Audit designed and reduced to 136 claims (`docs/audit/`); LLM check run on all 495 claims; Rishikesh's pilot done; human audit labels **pending** |
| At least six reviewers confirmed | **red** | Recruitment set aside by the team for now (decision 2026-10-20) |

**Gate: not passed.** `v0.3` is not tagged. Recovery plan (to agree with the mentor):
1. Finish the short human audit (about 30 minutes per member) this week; report NLI and LLM-check accuracy against it.
2. Restart reviewer recruitment when the team resumes it; until then the cut list's fallback applies (450 labels with four reviewers, Blueprint V2 §20).
3. Keep building Weeks 7 to 9 on judge labels, every number marked provisional, so the human labels plug into finished code.

## Numbers

| Measure | Value |
|---|---|
| Drafts for the full benchmark | 1,775 (99.9% valid), all judged, all with signal vectors |
| Red-team set | 40 attacks; 0 succeed on `draft-v2` with the output screen (5 did before the screen) |
| Security tests in CI | PII never reaches prompts, logs or stored artifacts; no cross-department retrieval; role matrix |
| LLM check vs NLI on 495 audit claims | 81.6% agreement; LLM supported / NLI not: 76; NLI supported / LLM not: 15 |

### Latency per stage (30 validation tickets, cache bypassed, GPU idle)

| Stage | Median | p90 |
|---|---|---|
| redact | 0.1 ms | 0.2 ms |
| classify | 24 ms | 105 ms |
| route | 48 ms | 85 ms |
| retrieve (hybrid + rerank, CPU) | 430 ms | 3,773 ms |
| draft (qwen2.5:7b, GPU) | 6,034 ms | 10,611 ms |
| check (NLI, GPU fp16) | 175 ms | 533 ms |
| signals | 0.2 ms | 0.6 ms |
| **total** | **6.8 s** | **19.2 s** |

Drafting is 89% of the time. Retrieval's p90 comes from the first reranker calls after a cold start.

### Baselines on validation (judge labels, PROVISIONAL)

| Baseline | AURC [95% CI] | AUROC |
|---|---|---|
| B0 always show | 0.244 [0.163, 0.341] | 0.500 |
| B1 verbalised | 0.197 [0.130, 0.274] | 0.622 |
| B2 token probability | 0.261 [0.158, 0.383] | 0.459 |
| **B4 top-1 similarity** | **0.173** [0.113, 0.248] | **0.644** |
| B5 reranker | 0.206 [0.133, 0.291] | 0.628 |
| B6 entailment share | 0.216 [0.129, 0.325] | 0.545 |
| B7 LR on B4+B5+B6 | 0.180 [0.107, 0.307] | 0.625 |

## Rishikesh
- PII redaction before every model call and log; security tests in CI.
- Output screen (`ai/security/output_screen.py`): URLs, commands and code in a step must come from a passage that step cites. Took the red team from 5/40 to 0/40, with no false blocks on benchmark drafts.
- `draft-v2` (a citation required on every step); device placement so the drafting LLM keeps the GPU; latency table.

## Aashritha
- Annotation tool v1: seeded planner, overlap pairs, adjudication, database uniqueness.
- 20 red-team tickets; RT-28's forbidden list corrected (it named `pg_wal`, which the real WAL article uses).
- Pilot and audit labelling pages.

## Shivaganesh
- Baselines B0 to B7 with group bootstrap; LLM groundedness check; reduced audit design (every disagreement plus 15 random agreements per member, with inclusion weights).

## Decisions and findings
- The reduced audit keeps a random sample of agreed claims; without it the audit could not estimate how often both checkers are wrong together.
- An AI-produced audit file was used only as a diagnostic, never as human labels.
- KB amendment 1 (three SAP articles corrected); the 164 drafts that cited them were regenerated.

## Open items (humans)
- Short audit: Rishikesh 40 claims, Aashritha 53, Shivaganesh 43 (`docs/audit/*_short.csv`).
- Pilot labels from Aashritha and Shivaganesh; human KB review (0/120); mentor sign-off; reviewers when resumed.
