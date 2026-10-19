---
id: DB-PERF-004
department: Database
topic: db-performance
title: Table keeps growing although rows are deleted
updated: '2025-06-24'
served: true
author: A
reviewer: null
---

## Symptom
A table's size on disk keeps growing and queries on it get slower, even though the
application deletes or updates old rows regularly.

## Cause
Updates and deletes leave dead row versions. Autovacuum normally cleans them so the space
can be reused. If autovacuum cannot keep up, or a long-running transaction stops it from
removing dead rows, the table bloats.

## Resolution steps
1. Check `n_dead_tup` and `last_autovacuum` for the table in `pg_stat_user_tables`.
2. Look for long-running or idle-in-transaction sessions in `pg_stat_activity`; they block
   cleanup.
3. Once those sessions end, run `VACUUM (ANALYZE)` on the table.
4. If autovacuum regularly falls behind on this table, ask the DBA team to tune its
   autovacuum settings.

## Warnings
`VACUUM FULL` rewrites the table under an exclusive lock; never run it on a busy table
without a maintenance window.

## Key facts
- Updates and deletes leave dead rows that autovacuum cleans up.
- Long-running transactions prevent dead rows from being removed.
- VACUUM FULL takes an exclusive lock on the table.
