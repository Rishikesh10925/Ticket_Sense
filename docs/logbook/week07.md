# Logbook — Week 7 (30 Nov to 6 Dec 2026): signal pipeline and labelling sprint 1

## Exit gate

| Condition | Status | Evidence |
|---|---|---|
| At least 300 human labels | **red** | 0. Outside reviewers not recruited (set aside by the team, 2026-10-20) |
| Kappa on overlap items ≥ 0.5 | **not measurable** | Needs the labels above |
| Features for every ticket | **green** | `signal_vectors`: features-v1 for all 1,775 drafts; model-side signals (B1, B2) for all, B3 for the 600 selected |
| Baseline curves on validation | **green (provisional)** | `docs/results/baselines-v1-judge.json`, judge labels |

## Built

| Who | What |
|---|---|
| Rishikesh | Signal vector (31 features over retrieval, reranker, grounding, consistency, routing, evidence and ticket groups), computed live and stored per draft; B1 verbalised confidence, B2 token probability (replayed from the cache), B3 self-consistency |
| Aashritha | Reviewer workbench start: reason codes and decision timer on every engineer action |
| Shivaganesh | Offline feature builder; judge labels for all 1,775 drafts; stratified selection of the 600 drafts to label (250 locked test, 200 calibration, 150 train/val) |

## Findings (provisional, judge labels)
- **The cheapest signal is the strongest single one.** Top-1 retrieval similarity (B4) has the lowest validation AURC (0.173); the model's own token probability (B2) is worse than chance (AUROC 0.459), and its stated confidence (B1) is high on almost every draft.
- **Unseen topics invert the retrieval signals.** On the unseen split (283 drafts, 99% unacceptable), top-1 similarity has AUROC 0.26: drafts for topics the KB does not cover still find confident-looking passages in the right department. This is the core shift problem the gate must handle (H3).
- **NLI grounding is weaker than expected** (B6 AUROC 0.545); the LLM-check comparison suggests it under-scores paraphrased instructions. The human audit decides.

## Open items
- Labelling sprint 1 waits on reviewers. The workbench, planner and selection are ready, so it can start the day reviewers are trained.
