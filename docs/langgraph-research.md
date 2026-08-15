# LangGraph orchestration pattern

Week 1 research note (Rishikesh) on how the ticket-processing pipeline described in
[architecture.md](architecture.md) will be implemented with LangGraph. No orchestration
code exists yet — this document records the pattern the team has agreed to build against
from Week 2 onward.

## Why LangGraph

The pipeline in `architecture.md` (classify → retrieve → draft → score confidence →
route) is a sequence of steps that each depend on the previous step's output, with one
conditional branch at the end (confidence gate → human review vs. escalation). LangGraph
models this naturally as a **state graph**: a single shared state object is threaded
through named nodes, each node reads/updates the parts of state it owns, and edges
(including conditional edges) decide what runs next. This avoids hand-rolling the control
flow, retry/error handling, and step ordering as ad-hoc Python, and keeps each pipeline
stage independently testable as a plain function of `(state) -> partial state update`.

## Planned graph shape

```text
                 ┌───────────────┐
   ticket ──────►│   classify    │  department, priority, sentiment
                 └───────┬───────┘
                         ▼
                 ┌───────────────┐
                 │    retrieve    │  embed ticket, fetch KB + resolved-ticket
                 └───────┬───────┘  evidence scoped to the routed department
                         ▼
                 ┌───────────────┐
                 │     draft      │  LLM drafts a cited reply constrained to
                 └───────┬───────┘  the retrieved evidence only
                         ▼
                 ┌───────────────┐
                 │     score      │  confidence classifier scores the draft
                 └───────┬───────┘  (retrieval relevance, similarity, freshness,
                         ▼           OCR confidence, category risk)
                 ┌───────────────┐
                 │  confidence    │  conditional edge
                 │     gate       │
                 └───┬───────┬───┘
                     ▼       ▼
              human review  human escalation
```

## State design

A single `TicketState` object (already sketched in `ai/graph/state.py` in an earlier
prototype, to be rebuilt from scratch) is expected to carry: the raw ticket, extracted
attachment text/OCR result, predicted department/priority/sentiment, retrieved evidence
chunks with their similarity scores, the drafted reply with citations, and the confidence
feature vector. Each node returns only the keys it adds or changes, which is the
standard LangGraph reducer pattern — it keeps nodes decoupled from each other's internals
and makes the state transitions inspectable for the resolution-replay/audit use case
described in `architecture.md`.

## Conditional routing, not a fixed threshold call inside a node

The confidence gate is modeled as a LangGraph **conditional edge** rather than an
if/else inside the scoring node itself, so the routing decision is visible in the graph
definition (and therefore in any graph visualization/trace) instead of being buried in
node logic. This matches the project's core requirement that the LLM never decides its
own confidence — the gate reads the confidence classifier's output and nothing else.

## What is deferred to later weeks

- The actual node implementations (`classify`, `retrieve`, `draft`, `score`) — this week
  only fixes the shape of the graph and the state contract between nodes.
- The confidence classifier itself, which the `score` node depends on.
- Checkpointing/persistence of graph runs, needed for the resolution-replay feature —
  LangGraph supports this via a checkpointer, to be selected once the Postgres schema for
  ticket history is finalized.

## References

- LangGraph documentation: state graphs, nodes, conditional edges, checkpointers.
- [architecture.md](architecture.md) — the data flow and schema this graph implements.
- [research-evaluation.md](research-evaluation.md) — evaluation protocol the graph's
  outputs will be measured against.
