# 5. Retrieval and generation

*Owner: Rishikesh. Draft v1.*

## 5.1 Department classification

MiniLM sentence embeddings plus TF-IDF features, logistic regression with balanced class
weights; the TF-IDF features were kept because they raised validation macro-F1 from 0.894
to 0.911 ([classifier-v2.json](../results/classifier-v2.json)):

| Split | Macro-F1 |
|---|---|
| Validation (known topics) | 0.911 |
| Unseen topics | 0.829 |

The cross-department probe (how well the next-best department matches) feeds the
confidence model and the shift guard.

## 5.2 Retrieval

Hybrid retrieval with oracle routing on 1,504 non-test tickets
([retrieval-v1.json](../results/retrieval-v1.json)):

| Type | Recall@5 | MRR | nDCG@10 |
|---|---|---|---|
| A | 1.000 | 0.997 | 0.998 |
| B | 1.000 | 0.995 | 0.996 |

Retrieval is close to perfect because the tickets paraphrase their gold article. This is a
property of a synthetic benchmark and is listed as a limitation; the interesting failures
are in routing and on unseen topics. No cross-department or withheld-article leakage was
found. Median hybrid latency is 419 ms (the reranker dominates).

## 5.3 Drafting

The drafting prompt (`draft-v2`) asks for JSON: numbered steps, each with the passage
numbers it relies on, or `can_answer: false` with the missing information. Drafts that fail
the schema are never shown. Throughput on the laptop GPU: 15.7 tokens/s, 3.4 s mean per
call ([llm-throughput-2026-10-19.json](../results/llm-throughput-2026-10-19.json)); a
ticket uses one call of about 1,440 tokens.

## 5.4 Claim checking

Each step is split into claims and each claim is scored by NLI against the passages it
cites ([draft_claims] table). The share of supported claims, the minimum support and the
mean support are confidence features; the three weakest claims are shown to the engineer
in the assisted lane.

**To be written**: two worked examples (one accepted, one escalated) with screenshots.
