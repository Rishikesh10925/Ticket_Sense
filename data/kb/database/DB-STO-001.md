---
id: DB-STO-001
department: Database
topic: db-storage
title: Database disk almost full
updated: '2026-04-14'
served: true
author: A
reviewer: null
legacy: disk-space-critical
---

## Symptom
Monitoring warns the database volume is nearly full, or the database already rejects
writes because the disk is full.

## Cause
Table and index bloat, write-ahead log (WAL) files piling up because a replication slot
or WAL archiving is stuck, or genuine data growth.

## Resolution steps
1. Find what uses the space: data files, or the `pg_wal` directory.
2. If `pg_wal` is large, check `pg_replication_slots` for inactive slots and WAL archiving
   for failures.
3. If writes are already failing, expand the volume first to restore service.
4. Then fix the cause: remove an abandoned slot (after the DBA confirms), fix archiving,
   or address bloat.

## Warnings
Never delete files from `pg_wal` by hand; it can make the database impossible to start.

## Key facts
- A growing pg_wal directory points to a stuck replication slot or failed WAL archiving.
- Expanding the volume restores service fast but does not fix the cause.
- Files in pg_wal are never deleted by hand.
