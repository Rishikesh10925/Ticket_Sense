---
id: DB-STO-004
department: Database
topic: db-storage
title: WAL archiving failing
updated: '2025-09-02'
served: true
author: A
reviewer: null
---

## Symptom
Monitoring reports WAL archive failures, and the `pg_wal` directory keeps growing.

## Cause
PostgreSQL keeps each WAL file until `archive_command` succeeds for it. If the archive
target is full, unreachable or its credentials expired, WAL files pile up locally.

## Resolution steps
1. Check `pg_stat_archiver` for `failed_count` and `last_failed_wal`.
2. Read the database log for the archive command's error message.
3. Fix the target: free space, restore network access, or renew the credential.
4. Confirm that archiving resumes and `pg_wal` shrinks as old files are archived.

## Warnings
Point-in-time recovery is broken while archiving fails; treat it as urgent.

## Key facts
- WAL files are kept until archive_command succeeds.
- pg_stat_archiver shows archive failures and the last failed WAL file.
- Point-in-time recovery is not possible while archiving is failing.
