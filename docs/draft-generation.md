# Draft generation

Week 6 note (Shivaganesh) on the draft-generation prompt, the default LLM provider,
and the groundedness check. Read this before `docs/groundedness-review.md` — the
review results only mean what this document says they mean.

## What the stub provider is (and isn't)

**No paid LLM API key is available in this project's environment.** `ai/generation/
llm_interface.py`'s `LLMProvider` is an abstract interface (`generate(prompt, evidence)
-> str`) so a real generative model can be plugged in later without touching any
calling code — but the only implementation that exists and has been tested is
`StubLLMProvider`, which is **deterministic and extractive**, not generative. It does
not call any language model. It pulls the most relevant text directly out of each
retrieved evidence item (a KB article's `## Resolution` section if it has one,
otherwise a resolved ticket's own description) and lists it with a citation marker.

This matters for how to read every result in this document and in
`docs/groundedness-review.md`:

- **It cannot hallucinate, by construction.** Every sentence in its output is copied
  (lightly cleaned up) from a retrieved passage, so "groundedness" for this provider is
  closer to a correctness check on the extraction/formatting code than a test of an AI
  model's tendency to make things up. A perfect groundedness score here is expected,
  not a hard-won result.
- **The groundedness checker itself (`ai/generation/groundedness.py`) is real,
  reusable infrastructure**, independent of which provider produced the draft — it just
  checks that every `[N]` citation marker in a draft text maps to a real evidence item,
  and flags any substantive line with no citation. It was verified against
  deliberately-broken synthetic drafts (an out-of-range citation, an uncited line) to
  confirm it actually catches problems, not just passes everything — see the "Checker
  self-test" section below.
- **When a real LLM provider is added**, this same checker becomes meaningful in the
  way it was originally intended: catching a generative model's citation of evidence
  that isn't actually there, or an unsupported claim slipped in alongside grounded
  ones. That's not been exercised here, since there is no generative provider to test
  it against.

## Prompt design

`ai/generation/prompt.py`'s `build_prompt(subject, description, evidence)` instructs
the model (a real one, if swapped in) to:

1. Answer using **only** the listed evidence — no outside knowledge.
2. Cite every claim inline with its bracketed number (`[1]`, `[2]`, ...).
3. Say so explicitly if the evidence doesn't fully answer the ticket, rather than
   guessing.

Evidence is numbered in the same order `retrieve_evidence` returns it (already ranked
by relevance — see `docs/retrieval.md`), so citation numbers map directly to retrieval
rank.

## Checker self-test

Before trusting `check_groundedness` against real drafts, it was run against two
synthetic cases to confirm it actually discriminates:

- A deliberately broken draft (one line citing `[3]` when only 2 evidence items exist,
  one line with no citation at all) — correctly flagged both: `ungrounded_markers=[3]`,
  one entry in `uncited_lines`.
- A correct draft citing both real evidence items — correctly passed
  (`is_fully_grounded = True`).

## Persistence

The generated draft (`ticket.ai_draft_reply`) and its citations
(`ticket.ai_draft_citations` — a JSON list of `{source_type, source_id, title}` per
citation number) are written to the ticket record by the LangGraph pipeline
(Week 6, Rishikesh — see `docs/langgraph-pipeline.md`), which advances the ticket's
status from `routed` to `drafted`.
