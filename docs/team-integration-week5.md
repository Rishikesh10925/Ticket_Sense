# Week 5 Team Integration

Evidence for the Week 5 milestone's Team Integration deliverable: "Run the retrieval
pipeline against 10 sample tickets across all five departments together and confirm no
cross-department leakage occurs (an SAP ticket must never retrieve HR content)."

## What this branch is

`week5-aashritha-evidence-display-ui` combines all three Week 5 member branches
(Shivaganesh's retrieval pipeline → Rishikesh's pgvector/API integration → Aashritha's
evidence UI, in that dependency order — retrieval needs embeddings, the API needs
retrieval, the UI needs the API), the same pattern as Week 4.

## Cross-department leakage check

Ran `retrieve_evidence` (the same function the live `/tickets/{id}/evidence` endpoint
calls) against 10 realistic sample queries, 2 per department, phrased the way an End
User would actually write them:

| Department | Sample queries |
|---|---|
| SAP | "Getting ME023 error trying to post a goods receipt in MIGO"; "My SAP account got locked after too many failed logins" |
| Networking | "VPN client hangs on connecting and never gets in"; "Office wifi keeps dropping every few minutes" |
| Cloud | "Getting access denied errors reading from an S3 bucket"; "Our EC2 instance is unreachable over SSH this morning" |
| Database | "App is throwing connection pool exhausted errors"; "A transaction just failed with a deadlock error" |
| HR | "How do I submit a request for time off next month"; "I can't find my payslip for this month in the portal" |

For each query, retrieved the top-5 evidence items scoped to that query's own
department, then independently looked up each returned item's actual department in the
database (not trusting the retrieval function's own labeling — checking the source of
truth) and compared.

**Result: 50/50 evidence items checked, 0 cross-department leakage instances.**

Every item retrieved for an SAP query actually belongs to SAP; same for all five
departments. This is the same guarantee already described in
[docs/retrieval.md](retrieval.md) (scoping happens in the SQL `WHERE` clause, not as a
post-filter), now confirmed against a broader, deliberately cross-department sample
rather than the single manual spot-check from earlier in the week.

## Mentor demo script

1. Log in as `customer@demo.local` (`Demo@123`).
2. Submit: subject "ME023 error on goods receipt", description "Getting ME023 item is
   blocked when trying to post a goods receipt in MIGO for a purchase order."
3. Click into the ticket — within a few seconds it shows `status: routed`,
   department `SAP`.
4. The "Retrieved evidence" panel shows the matching resolved ticket and KB article,
   each tagged `SAP` and its source type (Knowledge Base / Resolved Ticket).
5. For contrast, submit an HR-flavored ticket ("How do I submit a leave request") and
   confirm its evidence panel shows only HR content — never anything from the SAP
   ticket's evidence.

Logbook evidence: this document (cross-department leakage table above), plus
[docs/classification-metrics.md](classification-metrics.md)-style rigor applied to
retrieval in [docs/retrieval.md](retrieval.md)'s Recall@K section for the "Recall@K
measured" deliverable.
