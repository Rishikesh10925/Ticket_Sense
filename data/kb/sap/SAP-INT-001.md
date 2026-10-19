---
id: SAP-INT-001
department: SAP
topic: sap-interfaces
title: Background job not starting or stuck
updated: '2026-08-27'
served: true
author: S
reviewer: null
legacy: batch-job-stuck
---

## Symptom
A background job in SM37 stays "Released" or "Ready" and never becomes "Active", or it
stays "Active" for much longer than usual.

## Cause
"Released" means the job is waiting for its start condition (date, time or event).
"Ready" means the start condition is met but no background work process is free. A long
"Active" job is usually waiting on a database lock or processing far more data than usual.

## Resolution steps
1. Open the job in SM37 and note its status and planned start.
2. If "Released", check the start condition: a future start time or an event that has not
   been raised yet is normal.
3. If "Ready", check in SM50 whether all background work processes are busy. The job
   starts when one frees up. Report it to Basis if this persists.
4. If "Active" for too long, open the job log in SM37 and note the last step; check SM12
   for locks held by the job's user.
5. A job with no log progress for 30 minutes or more is cancelled by Basis, not the user.

## Warnings
Do not cancel and reschedule a running job without checking what it was posting; a
half-finished posting run can leave inconsistent documents.

## Key facts
- "Released" means waiting for the start condition; "Ready" means waiting for a free background work process.
- SM50 shows whether background work processes are busy.
- The job log in SM37 shows the last step a running job reached.
- Hung jobs are cancelled by Basis.
