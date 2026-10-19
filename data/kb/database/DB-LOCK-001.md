---
id: DB-LOCK-001
department: Database
topic: db-locking
title: Transaction fails with deadlock detected
updated: '2026-05-18'
served: true
author: A
reviewer: null
legacy: deadlock-detected-rollback
---

## Symptom
A transaction fails with "deadlock detected" and is rolled back, sometimes only under load.

## Cause
Two transactions lock the same rows in opposite order, each waiting for the other.
PostgreSQL detects this and cancels one of them. The data is safe; the cancelled
transaction must be retried.

## Resolution steps
1. Get the deadlock details from the database log: it shows both statements and the locks
   involved.
2. Look for code paths that update the same tables in a different order.
3. Ask the owning team to lock rows in a consistent order (for example by primary key) and
   to retry transactions that fail with a deadlock.
4. If a batch job collides with user traffic, move it to a quieter time or split it into
   smaller transactions.

## Warnings
A deadlock is not data corruption; do not restore backups because of one.

## Key facts
- A deadlock happens when two transactions lock the same rows in opposite order.
- PostgreSQL cancels one transaction; the application must retry it.
- The database log shows both statements in the deadlock.
- Locking rows in a consistent order prevents deadlocks.
