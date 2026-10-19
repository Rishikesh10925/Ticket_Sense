---
id: DB-LOCK-003
department: Database
topic: db-locking
title: Statement cancelled due to statement or lock timeout
updated: '2025-11-04'
served: true
author: A
reviewer: null
---

## Symptom
A query fails with "canceling statement due to statement timeout" or "canceling statement
due to lock timeout".

## Cause
The database cancels statements that run longer than `statement_timeout`, or wait for a
lock longer than `lock_timeout`. These limits protect the database from runaway queries
and long lock queues.

## Resolution steps
1. Note which message appeared: statement timeout means the query ran too long; lock
   timeout means it waited too long for another session.
2. For a statement timeout, get the query and analyse it (see the slow query article).
3. For a lock timeout, find what held the lock at that time, usually a long transaction
   or a migration.
4. If a specific report legitimately needs longer, the owning team can set a higher
   timeout for that session only.

## Warnings
Do not raise the timeout for the whole database to make one query pass.

## Key facts
- statement_timeout cancels queries that run too long.
- lock_timeout cancels statements that wait too long for a lock.
- A longer timeout is set per session for a legitimate job, never database-wide.
