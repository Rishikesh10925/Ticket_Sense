# Ticket classification and routing

Week 4 note (Rishikesh) on how a submitted ticket becomes classified and routed to a
department queue, closing the loop the state machine (`docs/ticket-lifecycle.md`) and
the trained classifiers (`docs/classification-model.md`) were both built for.

## Flow

```text
POST /tickets
  -> ticket saved, status = submitted, response returned immediately
  -> FastAPI BackgroundTask: classify_and_route(ticket.id)
       -> ai/models/classifier.py: classify_ticket(subject, description)
            -> department, priority, sentiment
       -> ticket.priority, ticket.sentiment set; status: submitted -> classified
       -> department looked up by name; ticket.department_id set; status: classified -> routed
```

The End User sees an immediate response (`status: submitted`) — classification isn't on
the request's critical path. A follow-up `GET /tickets/{id}` (or the Engineer polling
their queue) sees `status: routed` with `department_id`/`priority`/`sentiment` filled
in, typically within a second or two of the original request, satisfying the Week 4
"classified and routed automatically within a few seconds" requirement without needing
a task queue — Celery/Redis are explicitly out of scope for this project (see the root
README's Scope section), and a single `BackgroundTasks` call is sufficient at this
project's traffic scale.

## Why a background task, not a synchronous classification step

Classification runs a scikit-learn model — fast, but non-zero latency, and there's no
reason to make the End User's submission request wait on it. `FastAPI.BackgroundTasks`
runs the callback after the response is sent but within the same process, which is the
right amount of infrastructure for a capstone project: real asynchrony without standing
up a message broker.

## What happens if the department isn't found

`classify_and_route` looks up the predicted department name against the `departments`
table. If no matching row exists (shouldn't happen once the five departments are
seeded — see `backend/app/scripts/seed_demo_users.py` — but the model itself could in
principle return an unexpected label), the ticket is left in `classified` rather than
advancing to `routed`, with `department_id` unset. It doesn't crash the background task
or leave the ticket in an inconsistent state; it just doesn't reach the last lifecycle
step. Not currently surfaced to anyone as an error — worth adding an alert/log if this
turns out to happen in practice.

## Department-scoped queues

`GET /tickets` was already role-scoped since Week 3 (End User sees only their own
tickets, Department Engineer sees only their department's), but until classification
actually populated `department_id`, an Engineer's queue was always empty. Week 4 adds:

- **`?sort=priority`** — orders `high` → `medium` → `low` → unclassified, for the
  Engineer queue UI's "sortable by priority" requirement (Aashritha, Week 4).
- **`?department_id=`** — Admin-only (silently ignored for other roles, who are already
  scoped); lets Admin inspect any single department's queue instead of only the
  unfiltered firehose of every ticket.

No new routes were added — the existing `GET /tickets` endpoint already had the right
shape (list, filterable) from Week 3; Week 4 just adds the query parameters classification
made meaningful.

## Known limitation

The department classifier's accuracy is uneven across departments — see
[classification-model.md](classification-model.md). A ticket that's actually a
Database/Cloud/SAP issue can be misrouted more often than a Networking/HR one, simply
because the training data has far fewer real examples for those three. The pipeline
works; the model's per-department reliability doesn't yet, and that's visible in the
metrics rather than hidden.
