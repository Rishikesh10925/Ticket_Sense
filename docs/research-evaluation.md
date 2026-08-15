# TicketSense research evaluation

TicketSense is positioned as an integrated decision architecture, not as a claim that classification, RAG, or agent routing are individually novel.

## Reproducible experiment matrix

| Experiment | Baseline | TicketSense treatment | Primary metrics |
|---|---|---|---|
| Generation | Basic LLM | Multi-agent grounded generation | faithfulness, answer relevance |
| Retrieval | Vector-only top-k | hybrid lexical/vector + reranking | Recall@K, Precision@K, MRR |
| History | Raw closed tickets | structured problem/root-cause/resolution records | resolution acceptance |
| Autonomy | fixed threshold | calibrated risk-aware confidence | ECE, unsafe auto-resolution rate |
| Validation | generation only | evidence, policy, PII and safety gates | hallucination rate, overrides |
| Routing | round-robin | expertise, workload and SLA score | resolution time, reassignment rate |

## Evaluation protocol

Split tickets chronologically to prevent resolved-ticket leakage. Report organization-level macro averages and confidence intervals. Classification uses accuracy, macro precision/recall/F1. Retrieval uses labeled relevant sources with Recall@5, Precision@5 and MRR. RAG answers are graded for context relevance, faithfulness and answer relevance with a human-reviewed sample. Operational outcomes include acceptance, escalation, SLA breach and resolution time. Confidence calibration uses reliability bins and expected calibration error.

Never put synthetic example measurements into production analytics. Experiment outputs should carry dataset version, prompt version, model identifier, random seed and timestamp.
