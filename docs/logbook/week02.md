# Logbook — Week 2 (26 Oct to 1 Nov 2026): walking skeleton ★ M1, tag v0.1

## Exit gate

| Condition | Status | Evidence |
|---|---|---|
| A ticket travels UI → API → pipeline → database → queue with no manual step | green | `frontend/e2e/walking-skeleton.spec.ts` (Playwright), 10/10 passing runs against the Compose stack |
| Evaluation package passing its tests | green | 41 ai/ unit tests on main |

## Health dashboard

| Measure | Target (by week) | Now |
|---|---|---|
| KB articles in V2 template / human-reviewed | 120 / 120 (W3) | 18 on main (54 more on W3 branches) / **0 reviewed** |
| Benchmark tickets | ~1,800 frozen (W3) | 100 (prompt ticket-v2, SAP only) |
| CI on main | green | green |

## Rishikesh
- Migration 0011: KB `article_key`, `topic`, `served`, `version`. Withheld articles are excluded inside the retrieval SQL (test added).
- Measured the local model (schema-valid 10/10, logprobs 10/10) and wrote ADR 002 with a ~32 GPU-hour budget.

## Aashritha
- Playwright walking-skeleton test and `python tasks.py e2e`.
- Found and fixed a real bug: an aborted `/auth/me` call during reload cleared the session token, so users were logged out on refresh.

## Shivaganesh
- KB loader and template validator; ingestion matches V2 articles by id, sets topic and served flag, and lists or prunes stale V1 rows.
- 18 SAP articles in the V2 template (12 converted, 6 new). The unverifiable "ME023" code was removed.
- Style profile from the public dataset (aggregate statistics only).
- Ticket generator: types and labels set by construction; three prompt iterations after reviewing output:
  - v0: bodies median 12 words; B tickets dropped their extra question.
  - v1: B question appended in code; per-type quotas; copy check against hidden article text. Bodies still median 13 words.
  - v2: length enforced through the JSON schema (median 37 words); pasted logs may not contain the diagnosis; vague C2 tickets may not name the failing action; JSON-spill filter.
- Split manifest design: the leakage group is the gold article; C1 only in test or unseen.

## Problems and decisions
- The 7B model ignores word-count instructions; constrained decoding (array `minItems`) is what works.
- A local test database that ran a later branch's migration breaks `main`'s tests. Fix: drop `ticketsense_test`; the fixture recreates it.

## Open items for the team (humans)
- Fact-check the SAP batch (`docs/kb-authoring-workflow.md`) and set `reviewer:`.
- Fill in at least eight reviewer candidates.
- A and S: run `docker compose up -d --build` on your own machines.
