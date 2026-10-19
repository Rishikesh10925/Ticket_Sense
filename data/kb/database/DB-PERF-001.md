---
id: DB-PERF-001
department: Database
topic: db-performance
title: A query has become slow
updated: '2026-06-30'
served: true
author: A
reviewer: null
legacy: slow-query-performance
---

## Symptom
A report or application feature that used to be fast is now slow, gradually or suddenly
after a release or data growth.

## Cause
The query plan changed: a sequential scan over a large table instead of an index scan,
because an index is missing or table statistics are out of date. Sometimes the query does
far more work than needed.

## Resolution steps
1. Get the exact query from the application log or `pg_stat_statements`.
2. Run `EXPLAIN (ANALYZE, BUFFERS)` on it (on a replica or test copy if it changes data).
3. Look for a sequential scan on a large table where an index scan is expected.
4. If the index exists but is not used, refresh statistics with `ANALYZE` on the table.
5. If an index is missing or the query is inefficient, send the plan to the owning team.

## Warnings
Do not create indexes on production tables without the DBA team; building them can lock
the table.

## Key facts
- EXPLAIN ANALYZE shows the real plan and where time is spent.
- A sequential scan on a large table is the most common cause of a query that became slow.
- Outdated statistics are refreshed with ANALYZE.
