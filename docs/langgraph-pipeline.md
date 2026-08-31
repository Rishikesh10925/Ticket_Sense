# LangGraph pipeline

Week 6 (Rishikesh). Wires classification → routing → retrieval → draft generation into
a single LangGraph `StateGraph`, so a submitted ticket flows through all four stages
unattended and ends with a cited draft on the ticket record, ready for an engineer to
review. Implements the shape agreed in [langgraph-research.md](langgraph-research.md)
(Week 1) — the confidence-scoring node and gate sketched there are a later week; this
graph stops at `draft`.

## Graph shape

```text
   ticket ──► classify ──► route ──► retrieve ──► draft ──► END
```

- **classify** (`ai/graph/nodes.py::make_classify_node`) — calls
  `ai/models/classifier.py`'s `classify_ticket(subject, description)`, the same
  scikit-learn pipelines from Week 4. Returns predicted `department_name`, `priority`,
  `sentiment`.
- **route** (`make_route_node`) — looks up the `Department` row matching
  `department_name`. Returns `department_id`, or `None` if no department matches.
- **retrieve** (`make_retrieve_node`) — calls `ai/embeddings/retrieve.py`'s
  `retrieve_evidence`, department-scoped (Week 5). Returns `[]` with no department
  rather than guessing — same rule `app/services/retrieval.py`'s
  `get_evidence_for_ticket` already used for the on-demand evidence endpoint.
- **draft** (`make_draft_node`) — builds the prompt (`ai/generation/prompt.py`), calls
  the configured `LLMProvider`'s `generate()` (Week 6, Shivaganesh), and reads the
  citation markers (`[n]`) back out of the generated draft to build the persisted
  citations list — in the order the draft actually cited them, not just every
  retrieved item.

## Why closures, not graph state, for the DB session and LLM provider

LangGraph's `StateGraph` conventionally carries a plain, ideally-serializable
dict/TypedDict as its state (`ai/graph/state.py`'s `TicketState`) — that's what gets
diffed and merged between nodes, and what a checkpointer would persist if one were
configured (none is; see "What's deferred" below). A per-request `AsyncSession` and the
selected `LLMProvider` instance don't belong in that dict: they're run-scoped
dependencies, not ticket data. Instead, each node factory in `nodes.py` (e.g.
`make_route_node(db, department_model)`) closes over what it needs and returns a plain
`async def node(state) -> dict` function containing no state beyond what
`TicketState` declares. `ai/graph/pipeline.py`'s `build_pipeline()` is therefore a
cheap factory called once per ticket run (from
`backend/app/services/pipeline.py::run_ticket_pipeline`), not a singleton compiled
once at import time.

## LLM-provider abstraction

`ai/generation/llm_interface.py`'s `LLMProvider` ABC and
`ai/generation/provider_factory.py`'s `get_llm_provider(name)` mean the `draft` node
never hard-codes which backend generates text — it's selected by `LLM_PROVIDER` in
`.env` (`backend/app/config.py`'s `Settings.llm_provider`, default `"stub"`). Only
`StubLLMProvider` is registered today (**no paid LLM API key is available in this
project's environment** — see `llm_interface.py`'s module docstring and
[draft-generation.md](draft-generation.md) for what that does and doesn't mean for the
groundedness results). Adding a real generative provider later means registering a new
class in `provider_factory.py`'s `_PROVIDERS`; nothing that calls `generate()` changes.

## Persistence and lifecycle

`backend/app/services/pipeline.py::run_ticket_pipeline` runs as the ticket-creation
background task (replacing Week 4's `classify_and_route`, which stopped at `routed`;
that module has been deleted). After each stage it persists the result and advances
`Ticket.status` through the chain enforced by `ticket_lifecycle.transition()`:

1. `submitted → classified`: `priority`, `sentiment` persisted.
2. `classified → routed`: `department_id` persisted, only if a department matched.
3. `routed → drafted`: `ai_draft_reply` (the draft text) and `ai_draft_citations`
   (`[{"source_type", "source_id", "title"}, ...]`, new nullable JSONB column added in
   migration `0005_ticket_draft_citations`) persisted, only once routed — matching the
   existing rule that evidence retrieval needs a department to scope to.

If no department matches, the ticket deliberately stays at `routed`/`classified` and
un-drafted rather than drafting ungrounded — the same behavior the evidence endpoint
already had (empty evidence list) is now extended to skip drafting entirely.

## Hiding the draft from end users

TicketSense does not send AI-generated drafts to end users directly — a human engineer
always makes the final call (see [architecture.md](architecture.md)). `TicketOut` (the
`GET /tickets` / `GET /tickets/{id}` response schema) includes `ai_draft_reply` and
`ai_draft_citations`, but `app/schemas/tickets.py::build_ticket_out(ticket, role)`
returns them as `null` for the `end_user` role — computed on the response object, never
by mutating the underlying `Ticket` row, so nothing is actually lost server-side.

## What's deferred to later weeks

- The confidence-scoring node and confidence gate (conditional edge to human review vs.
  escalation) — see `langgraph-research.md`.
- A checkpointer for resolution-replay/audit — the graph currently runs start-to-finish
  in one `ainvoke()` call per ticket with no persisted intermediate graph state beyond
  what's written to the `tickets` table at the end of each stage.
- A real generative `LLMProvider` implementation.
