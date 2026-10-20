---
id: SAP-INT-004
department: SAP
topic: sap-interfaces
title: Scheduled job cancelled because a variant is missing
updated: '2025-12-16'
served: true
author: S
reviewer: Claude
---

## Symptom
A scheduled background job shows status "Canceled" in SM37, and the job log says the
variant does not exist or a selection field is invalid.

## Cause
The job runs a report with a saved variant. If the variant was deleted, renamed, or refers
to a value that no longer exists (for example a closed plant), the job cancels.

## Resolution steps
1. Open the job log in SM37 and note the report, the variant and the message.
2. Ask the job owner whether the variant was changed or deleted recently.
3. The owner recreates or corrects the variant, or updates the job step to use the right one.
4. Reschedule the job and check the next run finishes.

## Warnings
Do not rerun a cancelled posting job without asking the owner whether part of it already
ran.

## Key facts
- A job using a deleted or invalid variant ends with status Canceled.
- The SM37 job log names the report, the variant and the error.
- The job owner corrects the variant before the job is rescheduled.
