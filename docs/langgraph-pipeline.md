# LangGraph pipeline

Built in V1 (Weeks 6 to 9) and reworked for V2 in Week 5 (Rishikesh). It wires Blueprint
V2 §9 stages 1 to 8 into one LangGraph `StateGraph`. Every submitted ticket is
classified, routed, given hybrid-retrieved evidence, drafted as a structured cited
answer and claim-checked. A gate then decides whether the engineer sees the draft.

## Graph shape

```text
ticket ─► extract ─► classify ─► route ─► retrieve ─► draft ─► check ─► score ─►[gate]─┬─► show ─────┐
                                                                                       └─► escalate ─┴─► END
```

V1 scored *before* drafting so an escalated ticket was never drafted. V2 drafts every
ticket, because the claim check's support scores are inputs to the confidence model
(Weeks 7 to 8). An escalated ticket's draft is stored in `drafts` for evaluation and
never shown (§9.1: "no AI draft").

- **extract** (`make_extract_node`): `ai/ocr/extract.py` turns an image, PDF or log
  attachment into `attachment_text` and `ocr_confidence`.
- **classify** (`make_classify_node`): `ai/models/classifier.py`'s
  `classify_ticket(subject, description)` on the description plus attachment text.
- **route** (`make_route_node`): the `Department` row for the predicted name, or `None`.
- **retrieve** (`make_retrieve_node`): `ai/retrieval/hybrid.py`'s `hybrid_search`
  (keyword plus dense, RRF, cross-encoder rerank, scoped to the department and to served
  articles in the SQL). Every run is logged to `retrieval_runs`/`retrieval_hits`
  (`ai/retrieval/run_log.py`). Returns the numbered `passages` the drafter will see, the
  `retrieval_run_id`, the V1-shaped `evidence` list and the cross-department
  `retrieval_probe`.
- **draft** (`make_draft_node`): `ai/generation/drafting.py`'s `generate_draft`
  (prompt `draft-v1`). The model returns `{can_answer, steps[{text, citations}],
  missing_information}` under constrained JSON decoding. Injection defences:
  delimited data blocks, tag neutralising, an instruction hierarchy in the system
  prompt and schema rejection (a step without a citation, a citation to a passage that
  does not exist, or `can_answer` contradicting the steps). A draft is *shown* only if
  it validated and can answer. If the model server is unreachable, the node records the
  rejection and the ticket escalates rather than the pipeline crashing.
- **check** (`make_check_node`): `ai/grounding/claims.py`'s `check_draft` splits each
  step into claims and scores each claim's entailment by its cited passages with
  `cross-encoder/nli-deberta-v3-base`. Returns `groundedness` (the share of claims with
  support ≥ 0.5), min and mean support, every claim and the three weakest claims (the
  assisted lane shows these).
- **score** (`make_score_node`): the interim V1 confidence model and the department's
  threshold. The Week 8 confidence model replaces it.
- **gate** (`gate_condition`, a conditional edge): a draft that is not shown always
  escalates. Otherwise the score must clear the threshold. The Week 9 gate replaces
  this with the two Learn-then-Test thresholds and three lanes.
- **show** / **escalate**: set `gate_decision`. Database writes happen in
  `backend/app/services/pipeline.py`, not in the nodes.

### Configuration

| Setting | Values | Default |
|---|---|---|
| `LLM_CLIENT` | `ollama` (local GPU model, ADR 002), `stub` (offline extractive drafts) | `ollama` |
| `LLM_MODEL` | any Ollama model tag | `qwen2.5:7b-instruct` |
| `GROUNDING_SCORER` | `nli`, `lexical` (word overlap) | `nli` |

Tests and CI use `stub` and `lexical` (set in `backend/tests/conftest.py`), so they need
no model server and no NLI download. Neither is ever used for a reported result.

### Persistence

`run_ticket_pipeline` stores every structured draft in `drafts` (model, prompt
version, schema validity, `can_answer`, steps, evidence snapshot, groundedness and
retrieval run) and its claims in `draft_claims`, whichever way the gate went. Only a
shown draft is copied to `tickets.ai_draft_reply` as numbered steps with `[n]` markers,
with `ai_draft_citations` listing the cited articles in order. An escalation records
why: rejected draft, evidence cannot answer, or score below threshold.

## Attachment text feeds into classification and retrieval

`_augmented_description(state)` (`ai/graph/nodes.py`) appends any extracted attachment
text to the description for `classify` and `retrieve`, so a vague ticket ("Issue — see
attached") with an on-topic screenshot still routes and retrieves sensibly. The drafter
receives the attachment separately, in its own `<attachment>` data block.

## Why closures, not graph state, for the DB session and LLM client

`TicketState` (`ai/graph/state.py`) carries plain ticket data. A per-request
`AsyncSession`, the LLM client and the claim scorer are run-scoped dependencies, so each
node factory closes over what it needs. `build_pipeline()` is a cheap factory called
once per ticket run from `backend/app/services/pipeline.py::run_ticket_pipeline`.

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

## Reviewer UI

`TicketDetail.tsx` (Week 9, Aashritha) renders one of two mutually exclusive cards in
the department_engineer/admin view, based on `ticket.status`, never both:

- `status === "escalated"`: an "Escalation" card (`EscalationDetails`) fetches
  `GET /tickets/{id}/escalation` and shows the reason text plus the confidence score
  at the time, if any. If the ticket had a draft before a *reviewer* escalated it (as
  opposed to the gate sending it straight there), that original draft is shown
  underneath, read-only — there's nothing left to review once a ticket is escalated.
- otherwise: the existing "AI draft reply" card, with a `ReviewActions` component
  (`frontend/src/components/ReviewActions.tsx`) appended only when
  `status === "drafted"` — Accept/Edit/Reject/Escalate buttons that call
  `POST /tickets/{id}/feedback`. Edit and Reject switch to a textarea instead of
  submitting immediately (matching the backend's requirement that `edit` needs
  `edited_reply` and `reject` needs `reject_reason`); Accept and reviewer-Escalate fire
  immediately. On success the parent re-fetches the ticket, which naturally hides
  `ReviewActions` once `status` moves past `drafted`.

A ticket the gate sent straight to `escalated` never shows `ReviewActions` at all
(there's no `drafted` status in its history), and never shows a draft either, unless a
reviewer later escalates a ticket that *did* have one — the UI distinguishes "no draft
was ever generated" from "a draft existed but was escalated anyway" by checking
`ticket.ai_draft_reply` inside the Escalation card rather than assuming either case.

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
