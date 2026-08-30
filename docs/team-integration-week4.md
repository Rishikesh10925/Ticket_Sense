# Week 4 Team Integration

Evidence for the Week 4 milestone's Team Integration deliverable: "Integrate the trained
classification model into the live pipeline (branch `feature/ticket-classification`)
and confirm a newly submitted ticket is classified and routed automatically within a
few seconds."

## What this branch is

`feature/ticket-classification` combines all three Week 4 member branches:

- `week4-shivaganesh-ticket-classification` — trained/packaged department, priority,
  and sentiment classifiers (`ai/models/`)
- `week4-rishikesh-ticket-routing` — wires the classifiers into the live ticket
  pipeline as a background task, plus the department-scoped queue API
- `week4-aashritha-engineer-queue-ui` — the Engineer queue and ticket detail screens
  that surface the routing/classification results

They were built in that dependency order (each branched from the previous one's tip,
not independently from `main`), since — unlike prior weeks — this milestone's three
tasks genuinely depend on each other: routing needs a trained model to route with, and
the UI needs a live queue API to display.

## Integration test performed

Full rebuild of the Docker Compose stack (`docker compose up --build`) from this
combined branch, then, against the running containers (not a local dev shortcut):

1. Logged in as the seeded `customer@demo.local` account.
2. Submitted a ticket through the real form (`POST /tickets` via the frontend, with and
   without an attachment).
3. Confirmed the response returns immediately with `status: submitted`.
4. Polled `GET /tickets/{id}` and observed `status` advance to `routed` within a few
   seconds, with `department_id`, `priority`, and `sentiment` populated — the
   classification background task completing without any manual intervention.
5. Logged in as `engineer@demo.local` and confirmed the ticket appears in their queue
   (department-scoped, per Week 3's RBAC), sorted by priority.
6. Clicked into the ticket's detail screen and confirmed the department (resolved to a
   name via `GET /departments`, not a raw UUID), priority, and sentiment are all
   displayed.
7. Logged in as `admin@demo.local` and confirmed the same ticket is visible via
   `?department_id=` filtering.

This exercises the full path — real UI, real HTTP requests, real background
classification, real database, real second UI surface reading the result — not a
mocked or simulated version of any step.

## Known limitation carried into this integration

The department classifier's accuracy is uneven (see
[classification-model.md](classification-model.md)): a ticket with strong, unambiguous
department vocabulary (e.g. a VPN issue, an ME023 SAP error) routes correctly and
reliably; a short or ambiguous ticket can be misrouted, particularly to SAP or
Networking (the classes with more — or more distinctive — training signal). This was
observed directly during integration testing: two deliberately vague test tickets about
network issues were both routed to SAP instead of Networking. The pipeline mechanism
works correctly end-to-end; the model's per-ticket routing accuracy is the part that
still needs more real per-department training data, which is visible in the metrics
rather than hidden by the integration test only using easy examples.

## Mentor demo script

1. Log in as `customer@demo.local` (`Demo@123`).
2. Submit: subject "VPN not connecting from home", description "My VPN client hangs on
   connecting and never gets in, need this fixed today."
3. Wait ~3 seconds, refresh "My tickets" — status should read `routed`.
4. Log out, log in as `engineer@demo.local` (`Demo@123`).
5. The ticket appears in the Networking engineer's queue, marked `high` priority.
6. Click it — department (Networking), priority (high), and sentiment (negative) are
   all shown on the detail screen.

Logbook evidence: this document, plus
[classification-metrics.md](classification-metrics.md) for the classification metrics
table the roadmap's Mentor Review calls for.
