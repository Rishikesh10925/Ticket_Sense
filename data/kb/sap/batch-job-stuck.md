# Background Job Stuck in Released Status

**Department:** SAP

## Issue
A scheduled background job (SM37) stays in "Released" status and never moves
to "Active," or moves to "Active" and never completes.

## Resolution
1. Check SM37 for available background work processes — if all are consumed
   by other jobs, the new job will queue until one frees up.
2. If a work process is available but the job still won't start, check for a
   job with the same job name/user already running (duplicate lock).
3. For jobs stuck "Active" with no progress, check the job log (SM37 → Job
   Log) for the last step executed — this usually points to the exact
   program or database lock causing the stall.
4. Genuinely hung jobs (no log progress for 30+ minutes) should be cancelled
   by Basis, not by end users.

## Notes
Do not delete and reschedule a stuck job without checking whether it holds a
database lock — cancelling incorrectly can leave inconsistent postings.
