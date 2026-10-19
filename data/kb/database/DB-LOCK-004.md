---
id: DB-LOCK-004
department: Database
topic: db-locking
title: Schema change hangs and blocks the whole table
updated: '2026-03-09'
served: true
author: A
reviewer: null
---

## Symptom
An `ALTER TABLE` during a deployment hangs, and soon all queries on that table are blocked
too, causing an application outage.

## Cause
`ALTER TABLE` needs an exclusive lock. It waits behind any running transaction on the
table, and every new query then queues behind the waiting `ALTER TABLE`.

## Resolution steps
1. Cancel the waiting `ALTER TABLE` session to release the queue at once.
2. Find the long-running transaction it was waiting for.
3. Rerun the migration in a quiet window with a short `lock_timeout` (for example a few
   seconds), so it gives up instead of blocking everyone.
4. Retry the migration if it times out, rather than letting it wait.

## Warnings
Never run schema changes on busy tables without a lock timeout.

## Key facts
- ALTER TABLE needs an exclusive lock on the table.
- A waiting ALTER TABLE blocks every new query on that table behind it.
- Migrations set a short lock_timeout so they fail fast instead of blocking.
