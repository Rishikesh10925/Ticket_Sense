# Clearing an Orphaned Lock Blocking a Table

**Department:** Database

## Issue
Queries against a table hang indefinitely waiting on a lock, and the session
that appears to hold the lock is idle, disconnected, or otherwise not
actively doing anything.

## Resolution
1. Identify the blocking session (e.g. via `pg_locks`/`pg_stat_activity` on
   Postgres, joining blocked and blocking process IDs) rather than guessing
   which session holds the lock.
2. Check the blocking session's state — "idle in transaction" is the classic
   orphaned-lock pattern: a transaction was opened, a lock acquired, and the
   client disconnected or hung without committing or rolling back.
3. Confirm the session is genuinely stuck (not just slow) before terminating
   it — check how long it's been idle and whether it's associated with a
   known-hung client, not a legitimately long-running one.
4. Terminate the blocking session (e.g. `pg_terminate_backend`) once
   confirmed orphaned, which releases its locks immediately and unblocks the
   waiting queries.

## Notes
Recurring orphaned locks from the same application usually mean it isn't
reliably closing transactions on error paths — worth a follow-up with that
application's owners rather than just clearing the symptom each time.
