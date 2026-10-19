# Unexpected Cloud Cost Spike Alert

**Department:** Cloud

## Issue
A billing/cost anomaly alert fires for unexpected spend increase in a cloud
account or project.

## Resolution
1. Check the cost breakdown by service for the alert period — this usually
   immediately narrows the cause to one service (e.g., data transfer,
   compute, storage).
2. Common causes: a resource left running after a test (forgotten instance),
   a misconfigured auto-scaling group, or an increase in outbound data
   transfer.
3. If the spend is legitimate (planned load test, new deployment), document
   this in the ticket and close — not every spike is an incident.
4. If a resource is confirmed as unintentional, stop/terminate it and note
   which team owns the resource so they can prevent recurrence.

## Notes
Do not terminate resources without confirming ownership first — what looks
like a forgotten test instance may be a production dependency with a
misleading name.
