# Database Connection Timeout (RDS-style)

**Department:** Cloud

## Issue
Application logs show database connection timeouts or "too many
connections" errors against a managed database instance.

## Resolution
1. Check the database's current connection count against its configured
   max-connections limit — this is the most common direct cause of "too
   many connections."
2. Check for connections not being released properly by the application
   (connection pool misconfiguration or leaks) rather than assuming the
   database itself needs resizing.
3. Check recent CPU/memory metrics on the database instance — sustained high
   load can cause queries (and their connections) to back up.
4. If this coincides with a deploy, check whether the new version changed
   connection pool settings before escalating as a database-side issue.

## Notes
Increasing max-connections or instance size can mask a connection leak
rather than fix it — confirm the app is releasing connections properly
before treating this as purely a capacity issue.
