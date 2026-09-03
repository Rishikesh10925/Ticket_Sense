# Week 8 Team Integration

Evidence for the Week 8 milestone's Team Integration deliverable: "Review the first
confidence-model results together and jointly decide the initial per-department
threshold values before Week 9's gate is wired in."

## What this branch is

`week8-aashritha-confidence-display-ui` combines all three Week 8 member branches
(Shivaganesh's feature engineering + initial model → Rishikesh's pipeline
integration/schema/admin endpoint → Aashritha's confidence UI, the same dependency
order and pattern as every prior week).

## Step 1: review the model's own numbers

[confidence-model.md](confidence-model.md) / [confidence-metrics.md](confidence-metrics.md):
accuracy 0.54, ROC-AUC 0.605 on a 96/24 synthetic-label split. Weak but real — better
than the 0.50 random baseline, and the model's strongest learned coefficient
(`category_risk`, −2.27) matches the synthetic formula's own strongest weight, which
at minimum confirms the training pipeline recovers real signal rather than fitting
noise. See that doc's honest caveats before trusting these numbers as anything more
than "the pipeline works."

## Step 2: dry run — 10 real tickets, 2 per department

Submitted 10 tickets through the live API (typed descriptions this time, not
attachment-only — Week 7's dry run already covered that angle) and read back the
actual confidence score and feature breakdown the pipeline produced for each.

| Subject | Expected dept | Routed dept | Score | Category risk | Would pass decided threshold |
|---|---|---|---|---|---|
| VPN not connecting | Networking | Networking | 0.802 | 0.04 | yes |
| Wifi keeps dropping | Networking | Networking | 0.804 | 0.04 | yes |
| ME023 purchase order blocked | SAP | **HR** | 0.491 | 0.56 | no |
| SAP account locked | SAP | SAP | 0.470 | 0.71 | no |
| S3 access denied | Cloud | Cloud | 0.616 | 0.45 | yes |
| EC2 unreachable | Cloud | **Database** | 0.265 | 1.00 | no |
| Connection pool exhausted | Database | Database | 0.314 | 1.00 | no |
| Deadlock on transaction | Database | **SAP** | 0.418 | 0.71 | no |
| How to submit leave request | HR | HR | 0.560 | 0.56 | yes |
| Missing payslip | HR | HR | 0.557 | 0.56 | yes |

**10/10 tickets reached `drafted` unattended and 10/10 were scored** — the extended
pipeline (now six stages, ending in `score`) held up across all five departments in
one run.

**7/10 routed to the expected department; the 3 misroutes are the same
already-documented classifier weak spot** (Cloud/SAP/Database), not new this week.

**The score spread (0.265–0.804) tracks `category_risk` closely, and that alone is a
useful finding**: even the one **correctly**-routed SAP ticket ("SAP account locked",
0.470) scored below the old default threshold (0.5), because SAP's high `category_risk`
(0.71, from its 0.29 measured F1) pulls the score down regardless of how good the
retrieval was. This is the confidence model doing exactly what it's supposed to —
signaling low trust in a department the classifier itself is unreliable for, even when
this particular ticket happened to route correctly.

## Step 3: jointly decided per-department thresholds

Rationale, agreed together: since `category_risk` is the model's dominant learned
signal and it's derived directly from each department's measured classifier F1
([classification-metrics.md](classification-metrics.md)), the threshold should scale
the same way — a department the classifier is confidently accurate for can afford a
lower bar; a department it struggles with should require more evidence before a draft
reaches a human.

| Department | Classifier F1 | Category risk | Decided threshold | Was (default) |
|---|---|---|---|---|
| Networking | 0.96 | 0.04 | **0.45** | 0.50 |
| HR | 0.44 | 0.56 | **0.55** | 0.50 |
| Cloud | 0.55 | 0.45 | **0.55** | 0.50 |
| SAP | 0.29 | 0.71 | **0.65** | 0.50 |
| Database | 0.00 | 1.00 | **0.75** | 0.50 |

Set live via `PATCH /departments/{id}/threshold` (the real admin endpoint, not a
migration default) — verified in the dry-run script's output and re-confirmed with a
follow-up `GET /departments` read. Under these department-specific thresholds instead
of the flat 0.5 default, **5/10 of this dry run's tickets would pass** (both
Networking tickets, the Cloud S3 ticket, both HR tickets) — notably, the one
correctly-routed SAP ticket and the correctly-routed Database ticket both now fall
below their department's stricter bar, which is the intended effect: Week 9's gate
should escalate more readily in departments the classifier is worse at, independent of
whether any individual ticket happened to route correctly.

## No breakages found

As with prior weeks' integration passes, nothing needed a joint code fix — schema,
pipeline, scoring, persistence, the admin endpoint, and the UI all worked as designed
across all 10 dry-run tickets and the live threshold updates.

## What Week 9 inherits

- Real per-department thresholds are already live in the database — the gate doesn't
  need to invent defaults, just read `Ticket.confidence_threshold` (already snapshotted
  per ticket) against `Ticket.confidence_score`.
- The dry run above is a preview of exactly which kinds of tickets will escalate once
  the gate is wired in: anything in SAP/Database, and anything genuinely
  low-relevance/low-similarity in any department.

## Mentor demo script

1. Log in as `admin@demo.local` (`Demo@123`), open Admin → Departments, and show the
   per-department thresholds set above with their rationale (classifier F1 → risk →
   threshold).
2. Log in as `customer@demo.local`, submit "SAP account locked" (or any SAP-flavored
   ticket) and let it flow through unattended.
3. Log in as `engineer@demo.local`... — Networking's engineer won't see this one
   (it's SAP-routed); log in as an engineer seeded to SAP, or as Admin, and open the
   ticket to see the confidence panel: a score in the 0.4–0.5 range, well below SAP's
   0.65 threshold, with `category_risk` visibly the dominant bar.
4. Contrast with a Networking ticket ("VPN not connecting") — score ~0.80, comfortably
   above Networking's 0.45 threshold, `category_risk` bar nearly empty.

Logbook evidence: this document's dry-run table (initial precision/recall/ROC-AUC
reference in confidence-metrics.md) and the decided-thresholds table above.
