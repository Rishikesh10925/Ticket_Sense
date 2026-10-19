---
id: DB-PERF-002
department: Database
topic: db-performance
title: Index returns wrong results
updated: '2025-02-18'
served: true
author: A
reviewer: null
legacy: index-corruption-repair
---

## Symptom
Queries return inconsistent or clearly wrong results, or the log shows index errors.

## Cause
The index is corrupted, usually after a crash, power loss or a storage fault during a write.

## Resolution steps
1. Run the query again with index scans disabled for the session
   (`SET enable_indexscan = off; SET enable_bitmapscan = off;`). If the results differ, the
   index is at fault.
2. Rebuild it with `REINDEX INDEX CONCURRENTLY` so the table stays usable.
3. Find out why it happened: check the logs for crashes or storage errors.
4. If corruption comes back on the same storage, escalate to the storage team.

## Warnings
A plain `REINDEX` locks the table; use the concurrent form, or schedule a quiet window.

## Key facts
- Results that change with index scans disabled point to a corrupted index.
- Corrupted indexes are rebuilt, preferably with REINDEX CONCURRENTLY.
- Recurring corruption on one volume points to the storage, not the database.
