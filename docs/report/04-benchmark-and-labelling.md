# 4. Benchmark and labelling

*Owner: Shivaganesh. Draft v1. Details in the [datasheet](../datasheet.md).*

## 4.1 Knowledge base

120 articles across five departments (SAP, Cloud, Database, HR, Networking), written by the
team in a fixed template (symptom, cause, resolution steps, warnings). The 24 SAP articles
were fact-checked with AI assistance; the human second-member review of all 120 is
outstanding (Chapter 9).

## 4.2 Tickets

1,775 synthetic tickets from 596 scenarios, frozen on 2026-10-19 with SHA-256 hashes
([FREEZE_v1.json](../../data/benchmark/FREEZE_v1.json)). Four types:

| Type | Meaning | Correct behaviour | Share |
|---|---|---|---|
| A | Answerable from one served article | Correct, cited draft | 975 (54.9%) |
| B | Served article plus one extra question it cannot answer | Cautious draft or escalation | 265 (14.9%) |
| C1 | Written from a withheld article (6 topics, 24 articles not served) | Escalation | 355 (20.0%) |
| C2 | Vague, or an in-department request no article covers | Escalation or a request for information | 180 (10.1%) |

Splits are grouped by gold article, so paraphrases of one scenario never cross splits:
train 824, validation 135, calibration 262, locked test 271, unseen 283.

## 4.3 Labelling

- **Rubric** ([labelling-rubric.md](../labelling-rubric.md)): A acceptable, M minor edit,
  R major rework, W wrong or unsafe; A and M count as acceptable. Critical unsupported
  claims force R or W.
- **Selection**: 600 drafts, stratified: 250 locked test, 200 calibration, 150 train and
  validation; 150 double-labelled.
- **Tool**: a blinded annotation screen that never shows the score, lane, model or type.
- **Status**: 0 human labels collected so far. **To be filled**: counts, agreement
  (Cohen's kappa on the overlap, Fleiss' kappa on the pilot) and adjudication.

## 4.4 LLM-judge labels

`llama3.1:8b` labels every draft with the same rubric, for training volume and development
only. Against one team member on 28 pilot drafts: 82% binary agreement, kappa 0.58
([agreement-v1.json](../results/agreement-v1.json)). Headline results use human labels only.

## 4.5 Audit of the claim checker

A groundedness audit compares the two automatic claim checkers (NLI, and the
`llama3.1:8b` LLM check) with human labels. The three members labelled 136 of the 495
audit claims: every claim where the checkers disagree (88), plus a random sample of the
claims where they agree (43). Each sampled claim is weighted back to its stratum, and
5 claims marked `unclear` are left out
([audit-v1.json](../results/audit-v1.json), `ai/grounding/audit_report.py`).

| Checker | Accuracy | Says "supported" when the human says not | Says "not supported" when the human says supported |
|---|---|---|---|
| NLI (support at least 0.5) | 68% (95% CI 58 to 78) | 64% (45 to 79) | 13% |
| LLM check | 70% (59 to 80) | 79% (62 to 94) | 2% |

The humans judged about 64% of claims supported. Where the checkers disagree, the LLM
check is right more often (49 of 88, against 39 for NLI). Where they agree, both are
wrong on 11 of 43 sampled claims. Both checkers are lenient: most claims a human rejects
(an added command, a dropped condition, a different team) still pass. NLI support is
therefore a weak signal on its own, which is consistent with the confidence model's
reliance on many signals rather than one, and the claim checker should not be described
as a guarantee that a draft is grounded. The sample is small and the intervals are wide.
