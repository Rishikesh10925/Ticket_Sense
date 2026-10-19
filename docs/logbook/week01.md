# Logbook — Week 1 (19 to 25 Oct 2026): foundations, decisions, evaluation spine

## Exit gate

| Condition | Status | Evidence |
|---|---|---|
| Dataset decision made | green | [ADR 003](../adr/003-dataset-decision.md): fully synthetic with provenance |
| LLM provider and budget decided | green | [ADR 002](../adr/002-llm-provider.md): local qwen2.5:7b via Ollama, ~32 GPU-hours |
| All three members run the stack locally | amber | One command (`docker compose up -d --build`) verified on R's machine; A and S still to confirm on theirs |

## Health dashboard (Roadmap §9)

| Measure | Target (by week) | Now |
|---|---|---|
| KB articles authored / reviewed | 120 / 120 (W3) | 60 V1, 0 in V2 template |
| Benchmark tickets frozen | ~1,800 (W3) | 0 |
| CI status on main | green always | green |
| Logbook entries | one per member per week | 3 |

## Rishikesh
- Week 0 recovery report and audit decisions (`docs/plan/week0-recovery-report.md`).
- Removed customer auto-resolution: a human always decides (core rule of V2).
- Tests now run against an isolated `ticketsense_test` database; before this they truncated the dev DB.
- LLM client with Ollama backend, response cache and fake client (`ai/generation/llm.py`).
- CI: ruff, mypy, gitleaks, ai/ unit tests, backend tests on pgvector, frontend build. `main` green.
- Web service added to Compose; `tasks.py` + `Makefile`; API contract v0 and `docs/openapi.json`.
- ADR 001 (layout, workflow), ADR 002 (provider, budget); reading note on conformal risk control; definition of done.

## Aashritha
- Removed the auto-resolve zone from the threshold screen and customer copy.
- V2 wireframes: ticket form, queue with lane badges, three-lane workbench, blinded annotation tool, error-budget screen.
- Reviewer recruitment plan and invitation draft. **To do: fill in at least eight real candidate names.**
- ADR 004 (keep in-house components and tokens; TanStack Query from Week 4); reading note on selective classification.

## Shivaganesh
- Evaluation package `ai/evaluation`: risk-coverage, AURC, e-AURC, AUROC, ECE, Brier, reliability bins, group bootstrap, paired bootstrap, Learn-then-Test thresholds. 24 tests, 96% coverage.
- Taxonomy: 30 topics, 6 withheld (one per department plus a second Cloud topic; the blueprint's "six, one per department" is impossible with five departments).
- KB moved to `data/kb/`; article template and key-facts convention; ADR 003; rubric v0; pre-registration draft v0; reading note on Learn then Test.

## Decisions and parking lot
- Decision: per-member weekly branches merged into `main`, no pull requests (ADR 001).
- Parking lot: CRC-vs-LTT ablation for the Discussion chapter.

## Mentor evidence
Architecture, research questions and scope tiers walkthrough; ADRs 001 to 004. Mentor sign-off: _pending_.
