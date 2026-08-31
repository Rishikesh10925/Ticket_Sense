# Week 6 Team Integration

Evidence for the Week 6 milestone's Team Integration deliverable: "Full pipeline dry
run on 15–20 sample tickets across departments; fix any breakages found jointly."

## What this branch is

`week6-aashritha-draft-display-ui` combines all three Week 6 member branches
(Shivaganesh's draft-generation prompt/LLM interface/groundedness checker →
Rishikesh's LangGraph pipeline wiring/persistence → Aashritha's draft-display UI, the
same dependency order and pattern as Weeks 4 and 5).

## Dry run methodology

Submitted 20 tickets through the real running API (not a direct DB/function call —
`POST /tickets` as a genuine end_user, same as a real submission), 4 per department,
phrased the way an End User would actually write them. For each, polled
`GET /tickets/{id}` (as `admin@demo.local`, since the API nulls the draft fields for
the submitting end_user — see [langgraph-pipeline.md](langgraph-pipeline.md)) until it
reached `drafted` or timed out, then ran `ai/generation/groundedness.py`'s
`check_groundedness()` against the persisted `ai_draft_reply` and the ticket's actual
retrieved evidence (`GET /tickets/{id}/evidence`).

## Results

| Subject | Expected dept | Routed dept | Status reached | Fully grounded |
|---|---|---|---|---|
| ME023 error posting goods receipt | SAP | SAP | drafted | yes (5/5) |
| SAP account locked | SAP | SAP | drafted | yes (5/5) |
| Short dump in ST22 | SAP | SAP | drafted | yes (5/5) |
| IDoc stuck in status 51 | SAP | SAP | drafted | yes (5/5) |
| VPN not connecting | Networking | Networking | drafted | yes (5/5) |
| Wifi keeps dropping | Networking | Networking | drafted | yes (5/5) |
| New desk network port not working | Networking | **HR** | drafted | yes (5/5) |
| Cannot resolve internal hostnames | Networking | **HR** | drafted | yes (5/5) |
| S3 access denied | Cloud | Cloud | drafted | yes (5/5) |
| EC2 instance unreachable | Cloud | **Database** | drafted | yes (5/5) |
| Connection pool exhausted | Database | Database | drafted | yes (5/5) |
| Deadlock on transaction | Database | Database | drafted | yes (5/5) |
| Slow running query | Database | Database | drafted | yes (5/5) |
| How to submit leave request | HR | HR | drafted | yes (5/5) |
| Missing payslip | HR | HR | drafted | yes (5/5) |
| Benefits enrollment question | HR | HR | drafted | yes (5/5) |
| Onboarding checklist for new hire | HR | HR | drafted | yes (5/5) |
| Purchase order blocked for release | SAP | **Networking** | drafted | yes (5/5) |
| Site to site VPN tunnel down | Networking | Networking | drafted | yes (5/5) |
| Failed schema migration | Database | Database | drafted | yes (5/5) |

**20/20 tickets reached `drafted` unattended** — the pipeline itself (classify → route
→ retrieve → draft, all four LangGraph nodes, all four stages of lifecycle transition
and persistence) never broke or stalled across 20 back-to-back submissions.

**20/20 generated drafts were fully grounded** — every citation marker in every draft
maps to a real retrieved evidence item, and every evidence-based line carries at least
one citation. This is the automated version of the check behind
[groundedness-review.md](groundedness-review.md)'s manual 10-ticket review, now run
against double the sample size and freshly-submitted tickets rather than pre-selected
ones.

**16/20 tickets routed to the department the ticket was actually about.** The 4 misroutes
are a genuine finding, not a pipeline bug:

- **Groundedness and correctness are different things.** A misrouted ticket (e.g. "New
  desk network port not working" routed to HR) still produced a *fully grounded* draft
  — every citation legitimately traces back to a real HR knowledge-base article or
  resolved ticket. But those citations are grounded in the wrong problem's evidence,
  because retrieval is correctly scoped to whatever department classification chose,
  right or wrong (see [retrieval.md](retrieval.md) — no cross-department leakage was
  ever the guarantee; correct department selection is a separate, imperfect step). A
  reviewing engineer would immediately recognize an HR-flavored draft under a
  networking subject line as wrong, but this is exactly why the architecture never
  sends a draft straight to the requester (see [architecture.md](architecture.md)) —
  human review is load-bearing, not a formality.
- This is the same, already-documented department classifier imbalance from
  [classification-model.md](classification-model.md) (SAP/Cloud/Database have far fewer
  real training examples than Networking/HR), not a new defect introduced this week.
  No code changes were made in response to it — the fix belongs to Weeks 8–11's
  confidence model and human-review workflow, not to this week's pipeline wiring.

## No breakages found

Unlike Weeks 4 and 5's integration checks, this dry run didn't surface a bug that
needed a joint fix — the pipeline, LLM-provider abstraction, persistence, and draft
hiding all worked as designed across all 20 runs. The one issue found during
development (not this dry run) was the evidence-snippet truncation bug documented in
[groundedness-review.md](groundedness-review.md#quality-issues), already fixed and
re-verified before this integration pass.

## Mentor demo script

1. Log in as `customer@demo.local` (`Demo@123`).
2. Submit: subject "VPN not connecting from home", description "My VPN client hangs on
   connecting and never gets in, need this fixed today."
3. Click into the ticket — within a few seconds, unattended, it flows through
   `classified` → `routed` → `drafted` (shown to this role as "Draft in review").
4. Log out, log in as `engineer@demo.local` (`Demo@123`, Networking department).
5. Open the same ticket — the "AI draft reply" panel (side by side with "Retrieved
   evidence") shows the cited draft with hoverable `[n]` citation markers and a Sources
   list, none of it visible when logged in as the end user.
6. For the honest-limitations angle: submit "New desk network port not working" and
   show it lands in HR's queue instead of Networking's — a live example of the
   misrouting finding above, and why an engineer reviews before anything reaches the
   requester.

Logbook evidence: this document's results table and misrouting finding (groundedness
review notes), plus [groundedness-review.md](groundedness-review.md)'s deeper manual
read of citation correctness on a smaller hand-picked sample.
