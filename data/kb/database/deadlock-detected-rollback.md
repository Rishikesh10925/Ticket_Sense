# Deadlock-Triggered Transaction Rollback

**Department:** Database

## Issue
An application transaction fails with a deadlock error (e.g. Postgres
"deadlock detected") and is automatically rolled back, sometimes intermittently
under load and sometimes reliably for a specific operation.

## Resolution
1. Pull the deadlock detail from the database log — Postgres logs the exact
   queries and lock types involved (`log_lock_waits`/deadlock log entries),
   which is far faster than guessing from the application side.
2. Look for two transactions acquiring the same rows in a different order —
   the classic deadlock pattern is transaction A locking row 1 then waiting
   on row 2, while transaction B locks row 2 then waits on row 1.
3. Fix by enforcing a consistent lock acquisition order across all code paths
   that touch the same tables (e.g. always update rows in primary-key order).
4. If the deadlock is between a batch job and interactive traffic, consider
   moving the batch job to a lower-traffic window or breaking it into smaller
   transactions to reduce the lock window.

## Notes
A deadlock is not data corruption — Postgres always rolls back one of the two
transactions safely. The application must retry that transaction; a deadlock
error surfacing as a hard user-facing failure usually means the retry logic
is missing, not that the database did something wrong.
