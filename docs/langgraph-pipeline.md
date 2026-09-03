# LangGraph pipeline

Week 6 (Rishikesh), extended Week 7 (Rishikesh) to fold in attachment text, extended
Week 8 (Rishikesh) to add confidence scoring, extended Week 9 (Rishikesh) to add the
confidence gate. Wires attachment extraction → classification → routing → retrieval →
confidence scoring → **a gate that decides whether to draft at all** into a single
LangGraph `StateGraph`, so a submitted ticket flows through unattended and ends either
with a cited draft ready for an engineer, or an escalation with no draft shown. This is
the graph shape [langgraph-research.md](langgraph-research.md) (Week 1) originally
sketched, now fully implemented — the confidence-scoring node and the gate conditional
edge it deferred to later weeks are both built.

## Graph shape

```text
                                                          ┌──► draft ────┐
   ticket ──► extract ──► classify ──► route ──► retrieve ──► score ──►[gate]         ├──► END
                                                          └──► escalate ─┘
```

`score` runs **before** `draft` (this changed in Week 9 — Week 8 had `draft` then
`score`). Scoring only needs the retrieved evidence, OCR confidence, and routed
department — none of it depends on the draft's actual text — so the gate can decide
*whether to draft at all* instead of drafting first and discarding the result on a
failed gate. This also matches [architecture.md](architecture.md)'s "Example"
walkthrough literally: an escalated ticket has no AI draft, not a hidden one.

- **extract** (`ai/graph/nodes.py::make_extract_node`) — calls
  `ai/ocr/extract.py`'s `extract_attachment_text(path, attachment_type)` (Week 7,
  Shivaganesh: EasyOCR for images, `pypdf` for PDFs, plain read for logs). Returns
  `attachment_text`/`ocr_confidence`, both `None` if the ticket has no attachment. See
  [ocr-evaluation.md](ocr-evaluation.md) for quality notes.
- **classify** (`ai/graph/nodes.py::make_classify_node`) — calls
  `ai/models/classifier.py`'s `classify_ticket(subject, description)`, the same
  scikit-learn pipelines from Week 4, where `description` is
  `_augmented_description(state)` — the ticket's own description with any extracted
  attachment text appended, not `state["description"]` directly (see below). Returns
  predicted `department_name`, `priority`, `sentiment`.
- **route** (`make_route_node`) — looks up the `Department` row matching
  `department_name`. Returns `department_id`, or `None` if no department matches.
- **retrieve** (`make_retrieve_node`) — calls `ai/embeddings/retrieve.py`'s
  `retrieve_evidence`, department-scoped (Week 5). Returns `[]` with no department
  rather than guessing — same rule `app/services/retrieval.py`'s
  `get_evidence_for_ticket` already used for the on-demand evidence endpoint.
- **score** (`make_score_node`, Week 8) — computes the five confidence features
  (`ai/confidence/features.py::compute_features`, Shivaganesh) from the retrieved
  evidence, `ocr_confidence`, and routed department, then scores them with the trained
  model (`ai/confidence/predict.py::predict_confidence`). Also looks up the routed
  `Department`'s configured `confidence_threshold` (falling back to
  `DEFAULT_CONFIDENCE_THRESHOLD` if unrouted) and returns it alongside the score, so
  the threshold that was actually in force gets snapshotted onto the ticket rather than
  only living on the (mutable) `Department` row. See
  [confidence-model.md](confidence-model.md) for the model itself and
  [architecture.md](architecture.md) for why this is a separate model, never the
  drafting LLM's own self-assessment.
- **the gate** (`gate_condition`, Week 9) — a LangGraph *conditional edge* attached to
  `score`, not an if/else buried inside a node — reads `confidence_score` and
  `confidence_threshold` straight from state and routes to `"draft"` if the score
  clears the threshold, `"escalate"` otherwise. Deliberately a conditional edge rather
  than a branch inside `score` itself, so the routing decision is visible in the graph
  definition (see `docs/architecture.md`'s "Conditional routing, not a fixed threshold
  call inside a node"). Fails open to `"draft"` if score/threshold are somehow missing,
  rather than crashing the pipeline.
- **draft** (`make_draft_node`) — only runs if the gate passed. Builds the prompt
  (`ai/generation/prompt.py`) from `_augmented_description(state)`, calls the
  configured `LLMProvider`'s `generate()` (Week 6, Shivaganesh), and reads the citation
  markers (`[n]`) back out of the generated draft to build the persisted citations list
  — in the order the draft actually cited them, not just every retrieved item.
- **escalate** (`make_escalate_node`, Week 9) — only runs if the gate failed. A
  deliberately trivial node (`{"gate_decision": "escalate"}`) — creating the actual
  `Escalation` database row happens in `backend/app/services/pipeline.py`, not here,
  matching the established pattern that graph nodes read/compute but don't write to
  tables other than looking up `Department` (see "Why closures, not graph state"
  below).

## Attachment text feeds into classification, retrieval, and drafting

`_augmented_description(state)` (`ai/graph/nodes.py`) is what actually makes OCR text
useful rather than just a value sitting unused on the ticket record: `classify`,
`retrieve`, and `draft` all call it instead of reading `state["description"]`
directly. When `attachment_text` is present, it returns
`f"{description}\n\n[Extracted from attachment]\n{attachment_text}"`; otherwise it
returns `description` unchanged. This means a vague ticket ("Issue — see attached")
with an on-topic screenshot still classifies, routes, and retrieves sensibly, because
every downstream node sees the OCR'd error message, not just the two-word description
(see `backend/tests/test_graph_pipeline.py::test_classify_node_folds_in_attachment_text`
and the Week 7 Team Integration dry run for end-to-end confirmation).

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

0. `attachment_text`/`ocr_confidence` (nullable columns added in migration
   `0006_ticket_attachment_text_ocr_confidence`) persisted before classification —
   this doesn't advance `status` itself, it's just data attached to the ticket.
1. `submitted → classified`: `priority`, `sentiment` persisted.
2. `classified → routed`: `department_id` persisted, only if a department matched.
3. Once routed, `confidence_score`, `confidence_features` (the full five-signal dict),
   and `confidence_threshold` (nullable columns added in migration
   `0007_confidence_score_threshold_fields`) are always persisted — the gate always
   scores, on both branches. Then, based on `result["gate_decision"]`:
   - **`"draft"`**: `ai_draft_reply`, `ai_draft_citations`
     (`[{"source_type", "source_id", "title"}, ...]`, nullable JSONB column added in
     migration `0005_ticket_draft_citations`) are persisted, and status advances
     `routed → drafted`.
   - **`"escalate"`** (Week 9): no draft fields are touched — they stay `null`, per
     `architecture.md`'s "draft withheld". Status advances `routed → escalated`
     instead (migration `0008_ticket_escalated_status` added `escalated` to the status
     CHECK constraint and `ticket_lifecycle.py`'s valid-transitions map), and an
     `Escalation` row is created recording the reason (`"Confidence score {x} below
     department threshold {y}"`) and the triggering `confidence_score`.

If no department matches at all, the ticket deliberately stays at `routed`/`classified`
and un-drafted/un-scored rather than guessing — the same behavior the evidence endpoint
already had (empty evidence list) extends to skipping the gate entirely.

## Logging the gate's decision

Week 9's roadmap asks for "every gate decision (score, threshold, path taken)" to be
logged for later evaluation. Deliberately **no separate decision-log table** was
added: `Ticket.confidence_score`, `Ticket.confidence_threshold`, and `Ticket.status`
(`drafted` vs. `escalated`) already are that log, on the ticket record itself — a
query for "tickets whose gate escalated them" is just `WHERE status = 'escalated'`, and
the score/threshold that produced that outcome are sitting right there for evaluation
or retraining, no join needed. Adding a redundant append-only log table would duplicate
data already captured, for no evaluation capability this doesn't already provide.

## Reviewing a gated ticket

A ticket that reaches `drafted` is reviewed via `POST /tickets/{id}/feedback`
(`app/routers/tickets.py::submit_ticket_feedback`, Week 9) — a department_engineer or
admin records one of `accept`/`edit`/`reject`/`escalate`, which is logged to the
`feedback` table (the training signal `docs/confidence-labelling-guide.md` describes)
and advances status to `reviewed` (accept/edit/reject) or `escalated` (a reviewer
choosing to escalate a ticket that already had a draft — a second, human-initiated path
to `escalated`, distinct from the gate's own). `edit`/`reject` deliberately never
overwrite `Ticket.ai_draft_reply` — that column stays the AI's actual original output
(an audit trail), and the reviewer's edited text or rejection reason lives on the
`Feedback` row instead. A ticket that's already `escalated` (whichever path it took)
is read via `GET /tickets/{id}/escalation` — reviewer-only, same reasoning as hiding
`confidence_score` from `end_user`, since the reason references the score/threshold
that triggered it.

## Hiding the draft from end users

TicketSense does not send AI-generated drafts to end users directly — a human engineer
always makes the final call (see [architecture.md](architecture.md)). `TicketOut` (the
`GET /tickets` / `GET /tickets/{id}` response schema) includes `ai_draft_reply` and
`ai_draft_citations`, but `app/schemas/tickets.py::build_ticket_out(ticket, role)`
returns them as `null` for the `end_user` role — computed on the response object, never
by mutating the underlying `Ticket` row, so nothing is actually lost server-side.
`confidence_score`, `confidence_features`, and `confidence_threshold` are hidden the
same way (Week 8) — they judge a draft the end_user never sees, so showing them would
leak that judgment without the draft it's about. `attachment_text`/`ocr_confidence` are
**not** hidden this way — that's text extracted straight from the submitter's own
attachment, not an AI judgment about it, so every role that can see the ticket can see
it.

## Attachment storage and retrieval

Attachment storage (Week 3) was already in place — `POST /tickets` saves the uploaded
file under `settings.upload_dir/<ticket-scoped-uuid>/<original filename>` and records
the path on `Ticket.attachment_path`. Week 7 adds retrieval:
`GET /tickets/{id}/attachment` (`app/routers/tickets.py::get_ticket_attachment`)
streams the file back via `FileResponse`, using the same `_get_ticket_or_403` access
check as viewing the ticket itself, and 404s if the ticket has no attachment or the
file is missing on disk. `media_type` is left for `FileResponse` to infer from the
saved filename's extension, which is more precise than the coarse `image`/`pdf`/`log`
bucket `attachment_type` stores (that bucket is what OCR dispatch and the DB check
constraint care about, not the exact MIME type).

## What's deferred to later weeks

- A checkpointer for resolution-replay/audit — the graph currently runs start-to-finish
  in one `ainvoke()` call per ticket with no persisted intermediate graph state beyond
  what's written to the `tickets` table at the end of each stage.
- A real generative `LLMProvider` implementation.
- Retraining the confidence model on real Accept/Edit/Reject/Escalate outcomes instead
  of the Week 8 synthetic bootstrap labels, now that `feedback` rows are being produced
  by real reviewer actions — see Shivaganesh's Week 9 branch and
  [confidence-model.md](confidence-model.md).
