---
id: DB-LOCK-002
department: Database
topic: db-locking
title: Queries blocked by an idle session holding a lock
updated: '2026-08-24'
served: true
author: A
reviewer: null
legacy: orphaned-lock-blocking-table
---

## Symptom
Queries on a table hang waiting for a lock, and the session holding the lock is idle and
doing nothing.

## Cause
A session opened a transaction, took a lock, and then stopped without committing or
rolling back. It shows as "idle in transaction" and keeps its locks until it ends.

## Resolution steps
1. Find the blocking session with `pg_blocking_pids()` and `pg_stat_activity`.
2. Check its state and how long it has been idle in transaction.
3. Confirm with the owning application that the session is stuck, not a long legitimate job.
4. End it with `pg_terminate_backend(pid)`; its locks are released and waiting queries continue.
5. Ask the application team to close transactions on error paths.

## Warnings
Terminating a session rolls back its uncommitted work; confirm it is stuck first.

## Key facts
- A session "idle in transaction" keeps its locks until it ends.
- pg_blocking_pids() identifies the session blocking a query.
- pg_terminate_backend ends the session and releases its locks.
