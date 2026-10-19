# ADR 002: LLM provider, caching and budget

- Status: accepted
- Date: 2026-10-19
- Owner: Rishikesh
- Roadmap Week 1 exit gate: "LLM provider and budget decided"

## Context

The V1 pipeline never called a real model: its "drafts" were snippets extracted from
the evidence. V2 needs a model for drafting (§12.2), the LLM judge (§11.6), verbalised
confidence (B1), token log-probabilities (B2) and self-consistency samples (B3). The
project has no paid API budget. The team laptop has an NVIDIA RTX 5050 with 8 GB.

## Decision

1. **Local open-weight model via Ollama** (team decision, 19 Oct 2026).
   Drafting model: **`qwen2.5:7b-instruct`** (Q4, ~4.7 GB).
2. Every call goes through `ai/generation/llm.py`: one `LLMClient` interface
   (`OllamaClient` for real runs, `FakeLLMClient` for tests and CI), wrapped in
   `CachedLLMClient`. The cache is a SQLite file keyed by SHA-256 of
   (model, system prompt, user prompt, temperature, max tokens, seed, schema, logprobs),
   so a re-run of the benchmark costs nothing and is bit-for-bit reproducible.
   Sampled calls carry their seed in the key.
3. **Judge model differs from the drafting model** to reduce self-preference bias
   (Blueprint §13.5): `llama3.1:8b-instruct` is pulled in Week 4. Judge labels never
   decide headline numbers; humans do.
4. A hosted model can be added later as another `LLMClient` without touching callers.

## Measured capability (docs/results/llm-throughput-2026-10-19.json)

| Check | Result |
|---|---|
| Schema-constrained JSON (Ollama `format` = JSON Schema) | 10/10 valid |
| Token log-probabilities | 10/10 returned, so **B2 is not conditional** |
| Mean latency, short structured answer (~53 tokens) | 3.4 s (~16 tokens/s including prompt processing) |
| GPU memory | 5.2 GB of 8 GB |

## Budget estimate

Cost is GPU time, not money. Realistic sizes are about 1,500 prompt tokens (five
passages) and about 200 output tokens per draft. The measured rate scales that to
about **12 s per draft call**.

| Workload | Calls | Est. time |
|---|---|---|
| Drafts, 1,800 tickets | 1,800 | ~6 h |
| Self-consistency, 3 extra samples (cut-list item 3: five reduced to three up front) | 5,400 | ~18 h |
| Verbalised confidence (B1), short answer | 1,800 | ~2 h |
| Judge labels (llama3.1:8b), short verdict | 1,800 | ~3 h |
| Ticket generation (benchmark build) | ~1,800 | ~3 h |
| **Total** | **~12,600** | **~32 h of GPU time** |

That is about four overnight runs, spread over Weeks 3 to 7. The cache means none of it
is repeated. Five consistency samples (instead of three) would add about 12 h. That
option stays open if Week 7 has slack.

## Consequences

- Draft quality is lower than a frontier hosted model. The method is what's under test,
  not the drafter. A weaker drafter produces more unacceptable drafts, which makes the
  gate's job harder and more informative. The report states the model used.
- Offline reproducibility (extended-tier item) comes for free.
- Runs are tied to one machine with a GPU. Other members reproduce from the cache file,
  which is shared with each experiment record.
