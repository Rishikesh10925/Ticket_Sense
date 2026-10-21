# Latency and cost (Week 10)

- Owner: Rishikesh. Roadmap Week 10: "latency and cost report".
- Data: [`docs/results/latency-v2.json`](results/latency-v2.json), produced by
  `python ai/evaluation/latency.py --n 30` on 2026-10-21. It ran 30 seeded validation
  tickets plus one warm-up, with the response cache bypassed and the GPU otherwise idle.
- Machine: the development laptop (NVIDIA GeForce RTX 5050 Laptop GPU, 8 GB; recorded in
  [`llm-throughput-2026-10-19.json`](results/llm-throughput-2026-10-19.json)), with Ollama
  serving `qwen2.5:7b-instruct`. NLI claim check on the GPU; embeddings and reranker on the CPU.

## Latency per stage

| Stage | Median (ms) | p90 (ms) | Max (ms) |
|---|---:|---:|---:|
| redact | 0.1 | 0.1 | 0.2 |
| classify | 27.5 | 33.7 | 63.4 |
| route | 53.3 | 59.5 | 68.9 |
| retrieve | 477.0 | 555.9 | 566.5 |
| draft | 5,684.9 | 6,854.3 | 7,626.5 |
| check | 176.9 | 261.0 | 468.4 |
| signals | 0.2 | 0.3 | 0.5 |
| gate | 5.6 | 7.2 | 18.4 |
| **total** | **6,436.1** | **7,688.7** | **8,544.9** |

- Drafting is 88% of the median total. Everything the project added around the model
  (redaction, routing, retrieval, the claim check, the signals and the confidence gate) costs
  about 0.75 s per ticket.
- The confidence gate itself adds a median 5.6 ms.
- Compared with Week 6 ([`latency-v1.json`](results/latency-v1.json), no gate stage), the
  median total is similar (6.8 s then, 6.4 s now) and the tail is much shorter (p90 19.2 s
  then, 7.7 s now), mostly from retrieval (p90 3.8 s then, 0.56 s now). Why the Week 6
  tail was longer was not recorded: **To be documented**.
- The first ticket after a restart loads every model and takes far longer. It is excluded
  as a warm-up here, and the demo storyboard warms up before presenting.

## Cost per ticket

Everything runs locally, so a ticket has no per-call fee. Its cost is the compute it uses:

| Measure | Value |
|---|---:|
| Language-model calls | 1 |
| Prompt tokens (median) | 1,301 |
| Completion tokens (median) | 166 |
| Total tokens (mean) | 1,440 |
| GPU time for drafting (median) | about 5.7 s |

- With a hosted model instead, the cost per ticket would be these token counts times that
  provider's prices. No price is assumed in this report: **To be documented** if a hosted
  deployment is ever compared.
- The claim check uses an NLI model, not the language model, so groundedness adds no tokens.
- Lanes in this sample: 20 assisted, 10 escalated, 0 fast. The fast lane has no certified
  threshold yet. Escalated tickets are still drafted (their drafts feed the evaluation),
  so every ticket costs one drafting call.

## Limitations

- One laptop, one sample of 30 tickets: the numbers show the order of magnitude, not a
  capacity plan.
- Tickets ran one at a time; throughput under concurrent load is not measured.
