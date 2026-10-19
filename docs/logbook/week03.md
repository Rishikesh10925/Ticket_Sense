# Logbook — Week 3 (2 to 8 Nov 2026): data engine, pre-registration, security basics

## Exit gate

| Condition | Status | Evidence |
|---|---|---|
| Benchmark generated, validated and frozen with hashes | green (provisional) | `data/benchmark/FREEZE_v1.json`; `python ai/benchmark/freeze.py verify --version v1`; CI test `test_frozen_benchmark_v1_is_unchanged` |
| Zero leakage across splits | green | `validate_benchmark.py`: GREEN (provenance, split rules, no gold article in two splits) |
| Pre-registration committed before any label | green | `docs/prereg.md` v1, tag `prereg-v1` |
| All 120 articles human-reviewed | **red** | 0/120 `reviewer:` set; `validate_benchmark.py --require-review` is RED, so the freeze is marked provisional |

## Health dashboard

| Measure | Target | Now |
|---|---|---|
| KB articles in V2 template / human-reviewed | 120 / 120 | 120 / **0** |
| Benchmark tickets | ~1,800 frozen | 1,775 frozen (596 scenarios) |
| Types A / B / C1 / C2 | 55 / 15 / 20 / 10 % | 54.9 / 14.9 / 20.0 / 10.1 % |
| Splits train / val / calib / test / unseen | ~900 / 150 / 250 / 250 / C1 | 824 / 135 / 262 / 271 / 283 |
| CI on main | green | green |

## Rishikesh
- `kb_chunks` with a generated tsvector (GIN) and an HNSW index; ingestion writes chunks for seeded and admin-authored articles.
- Role-matrix tests (21 checks), including annotators being blocked from every ticket endpoint.

## Aashritha
- All Cloud, Networking and HR articles in the V2 template.
- Annotation tool design (`docs/annotation-tool.md`) and the reviewer recruitment plan.

## Shivaganesh
- Benchmark v1: 1,775 tickets, generated with `qwen2.5:7b-instruct`, prompt `ticket-v2`. 209 attempts rejected by the quality checks and regenerated; 28 paraphrases failed every retry and were dropped rather than kept.
- Split manifest (seed 2026, leakage unit = gold article), benchmark validator, freeze script (`write` / `verify`; the KB hash ignores the `reviewer:` line so recording a fact-check does not count as a content change).
- Datasheet and pre-registration filled with the frozen counts; amendment log started.
- TF-IDF baseline on the train split, scored on validation: department macro-F1 0.761, priority macro-F1 0.313.

## Findings
- **Priority is barely learnable from the text** (macro-F1 0.31, near chance). Priority is assigned in code before generation and the generated wording rarely signals it. Classifier v2 (Week 4) should report priority with this caveat; it is not a classifier failure.
- **Some type-A tickets hint at the cause in their own words** (spot check: an SAP date-format ticket names the article's cause). The 5-word copy check cannot catch paraphrase. Recorded in the datasheet; the Week 4 retrieval evaluation measures how much easier this makes type A (risk R4).

## Problems and decisions
- The first generation run died when Ollama auto-updated mid-run, the second when the terminal was closed. The LLM client now retries dropped connections with backoff, and Ollama runs as a detached app.
- After the update, Ollama started on the CPU (the laptop GPU was not detected at that start). Restarting it found the GPU; throughput went from ~3 to ~15 calls a minute.
- Benchmark hashes are computed with LF line endings so Windows checkouts and CI agree.

## Open items for the team (humans)
- **Fact-check all 120 articles** and set `reviewer:` to a member other than the author. Any article changed by the check means regenerating its tickets and refreezing as v1.1 (pre-registration amendment first).
- Fill in at least eight reviewer candidates and send the invitations (Week 3 step of `docs/study/reviewer-recruitment.md`).
- Mentor sign-off on the pre-registration.
