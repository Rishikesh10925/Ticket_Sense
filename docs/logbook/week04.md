# Logbook — Week 4 (9 to 15 Nov 2026): routing and hybrid retrieval ★ M2, tag v0.2

## Exit gate

| Condition | Status | Evidence |
|---|---|---|
| Recall@5 ≥ 0.80 on type A | green | Hybrid R@5 **1.000** on 847 type-A tickets (all splits except the locked test, gold-department routing); `docs/results/retrieval-v1.json` |
| Zero leakage | green | 0 cross-department hits and 0 withheld-article hits in all four configurations |
| Classifier v2 integrated, with uncertainty in pipeline state | green | `make_classify_node`: labels plus max probability, normalised entropy and class probabilities; 149 backend tests pass |

## Health dashboard

| Measure | Target | Now |
|---|---|---|
| KB articles human-reviewed | 120 | **0** |
| Department routing macro-F1 (val) | beat baseline 0.761 | **0.911** (unseen topics 0.829) |
| Priority macro-F1 (val) | — | 0.402 (baseline 0.313) |
| CI on main | green | green |

## Retrieval results (benchmark v1, excluding the locked test)

| Config | R@5 (A) | MRR (A) | nDCG@10 (A) | MRR (B) | Median latency |
|---|---|---|---|---|---|
| Keyword (tsvector) | 1.000 | 0.979 | 0.984 | 0.978 | 15 ms |
| Dense (MiniLM, HNSW) | 1.000 | 0.992 | 0.994 | 0.993 | 13 ms |
| Fused (RRF k=60) | 1.000 | 0.991 | 0.994 | 0.993 | 16 ms |
| **Hybrid** (fused + cross-encoder rerank) | **1.000** | **0.997** | **0.998** | 0.995 | 419 ms |

## Rishikesh
- Hybrid retrieval (keyword + dense, RRF, cross-encoder rerank of the top 20 to 5), department and served filters inside the SQL, cross-department probe, every run logged with all candidate scores.
- Live pipeline and evidence endpoint switched to logged hybrid retrieval.
- Retrieval evaluation on benchmark v1.

## Aashritha
- Annotation tool v0: blinded item view, keyboard labels, timer; annotator role locked out of tickets.
- Engineer queue on TanStack Query with background refresh; lane tokens and badge.

## Shivaganesh
- Classifier v2 (MiniLM embeddings plus TF-IDF, logistic regression), selected on validation, reported on unseen topics; now routes live tickets.
- LLM judge v0.

## Findings
- **Retrieval on this benchmark is saturated (risk R4 confirmed).** Every configuration finds the gold article in the top 5 for every answerable ticket; even plain keyword search has MRR 0.98. Tickets are written from the article's symptom and cause, and each department has only 19 served articles. Consequences:
  - Retrieval quality cannot separate good from bad drafts on type A. Top-1 similarity (baseline B4) will mainly separate *answerable* (A, B) from *unanswerable* (C1, C2) tickets, which is exactly the gate's job, so the research question survives.
  - The reranker adds 400 ms for a gain that only shows in MRR (0.991 → 0.997). Kept, because its score is baseline B5 and a confidence feature.
  - The report must say retrieval numbers are an upper bound, not a production estimate.
- **The cross-department probe barely varies by type** (mean best similarity elsewhere: A 0.363, B 0.363, C1 0.358, C2 0.321). It may still help as one feature among many; the Week 8 ablation that drops it will tell.
- **Classifier pickles must use the package path** (`models.classifier_v2`), or the live pipeline cannot load them. Fixed in the training script.

## Open items for the team (humans)
- Fact-check the 120 articles; recruit and confirm reviewers (Week 6 gate needs at least six).
