# Application Errors From an Exhausted Connection Pool

**Department:** Database

## Issue
Application logs show "connection pool exhausted", "too many clients already",
or requests timing out waiting for a database connection, even though the
database server itself is up and reachable.

## Resolution
1. Check the database's current connection count against its configured max
   (`SHOW max_connections` on Postgres) — confirm whether the server is
   actually at its limit or whether the application's own pool is
   misconfigured with too small a size.
2. Look for a connection leak: a code path that opens a connection/session
   and never closes or returns it to the pool (common after an unhandled
   exception between acquiring and releasing a connection).
3. Check for idle-in-transaction connections holding a slot open — these
   count against the limit even when doing no work.
4. As an immediate mitigation, restart the affected application instance to
   release leaked connections while the leak itself is investigated; this is
   a workaround, not a fix.

## Notes
A sudden spike in "pool exhausted" errors after a deploy usually points to a
new code path missing a `finally`/context-manager close — check the most
recent deploy first.
