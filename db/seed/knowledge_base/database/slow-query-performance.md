# Triaging a Slow-Running Query

**Department:** Database

## Issue
A specific query or application feature has become noticeably slower, either
gradually over time or suddenly after a deploy or data growth.

## Resolution
1. Get the exact query (from application logs or slow-query log) and run
   `EXPLAIN ANALYZE` against it to see the actual execution plan and where
   time is being spent, rather than guessing.
2. Check whether the plan is doing a sequential scan on a large table where an
   index scan would be expected — this is the single most common cause of a
   query that "used to be fast."
3. If an index exists but isn't being used, check whether table statistics are
   stale (`ANALYZE` the table) — the planner can pick a bad plan based on
   outdated row-count estimates.
4. If the query is fundamentally doing more work than it needs to (e.g.
   fetching full rows to check existence, or an N+1 pattern from the
   application layer), the fix is in the application, not the database.

## Notes
"It was fast yesterday" is a strong signal to check for a recent data volume
change or a recent schema/index change — don't assume it's an intrinsic query
problem without checking what actually changed.
