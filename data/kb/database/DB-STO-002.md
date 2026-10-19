---
id: DB-STO-002
department: Database
topic: db-storage
title: Backup before a change or restore after data loss
updated: '2026-01-20'
served: true
author: A
reviewer: null
legacy: backup-restore-request
---

## Symptom
A team asks for a backup before a risky change, or for a restore after data was lost (a
bad migration, or an `UPDATE` or `DELETE` without a `WHERE` clause).

## Cause
Scheduled backups and continuous WAL archiving allow point-in-time recovery to any moment
inside the retention window.

## Resolution steps
1. For a pre-change backup, take an on-demand backup and give the requester the backup ID
   and time before they start.
2. For a restore, get the exact time the bad change happened from logs or the requester.
3. Restore to a new database or instance at a point just before that time.
4. Let the requester verify the data, then copy the needed rows back or plan a cut-over
   window with them.

## Warnings
Never restore over the live database before the restored copy is verified.

## Key facts
- Point-in-time recovery can restore to any moment inside the retention window.
- Restores go to a new database first, never directly over the live one.
- The exact time of the bad change sets the restore point.
