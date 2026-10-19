---
id: DB-STO-003
department: Database
topic: db-storage
title: Nightly database backup failed
updated: '2026-07-27'
served: true
author: A
reviewer: null
---

## Symptom
The backup monitoring reports that last night's backup of a database failed or did not run.

## Cause
Common causes are not enough space in the backup target, an expired credential for the
backup storage, a backup that overlapped a heavy batch job and timed out, or the
database being unreachable at the time.

## Resolution steps
1. Read the backup job's log for the exact error.
2. Fix the cause: free space or extend the target, renew the storage credential, or move
   the schedule away from the batch job.
3. Run an on-demand backup at once, so there is a recent good backup.
4. Confirm the new backup completed and its size is similar to previous ones.

## Warnings
A failed backup is not "fixed" until a new backup has completed successfully.

## Key facts
- The backup job log gives the reason for a failed backup.
- After fixing the cause, an on-demand backup is run immediately.
- A backup much smaller than usual should be investigated.
