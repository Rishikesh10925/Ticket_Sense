# Logbook — Week 9 (14 to 20 Dec 2026): confidence gate and human review workflow

## Exit gate

| Condition | Status | Evidence |
|---|---|---|
| High-confidence drafts reach a reviewer, low-confidence tickets are escalated, all decisions logged | **green** | Gate lanes (fast / assisted / escalate) with score, threshold and reasons stored per draft; `GET /tickets/{id}/decision` |
| Live demo: one ticket reaches review, one is escalated, reviewer acts on both | **green** | [team-integration-week9.md](../team-integration-week9.md): 6 tickets, each member acted as reviewer |
| Shift guard for unseen topics | **green (provisional)** | [shift-v1-judge.json](../results/shift-v1-judge.json): tuned on three withheld topics, tested on three others |

## Results (PROVISIONAL: LLM-judge labels)

- **Shift guard** (department probability ≥ 0.5, probe margin ≥ 0.1), chosen on the tuning
  topics: unseen-topic drafts shown fall from 77 to 33 of 149, and every one of them was
  unacceptable either way.
- **Red team through the full pipeline and gate:** 0 of 40 injection tickets reach an
  engineer; the screen blocks 13 before drafting ([redteam-v3-pipeline.json](../results/redteam-v3-pipeline.json)).

## Rishikesh
- Gate loads the shift guard together with a certified threshold set.
- Red team run end to end; screen-v2 blocks terms the evidence only warns against.
- Lane analytics: lane mix, engineer actions, latency and confidence per lane.

## Aashritha
- Reviewer workbench laid out per lane: fast, assisted (weakest claims shown first), escalate.
- Two matched user-study ticket sets that avoid all labelled and pilot tickets; study
  protocol, session script, consent form and SUS.

## Shivaganesh
- Shift guard tuned on three withheld topics and tested on the other three.
- The gate's top reasons are kept distinct; confidence results regenerated.
- Error analysis of the gate's worst shown cases ([error-analysis-v1-judge.md](../results/error-analysis-v1-judge.md)).

## Findings
- **The fast lane stays closed.** Learn-then-Test certifies no fast threshold on the
  calibration labels, so every answering draft goes to the assisted lane or is escalated.
- **The guard helps, but does not fix unseen topics:** it halves exposure and still lets
  unacceptable drafts through.
