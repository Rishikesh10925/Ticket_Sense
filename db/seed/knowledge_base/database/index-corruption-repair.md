# Detecting and Repairing a Corrupted Index

**Department:** Database

## Issue
Queries against a table return inconsistent or clearly wrong results, or the
database logs index-related errors, suggesting a corrupted index rather than
an application bug.

## Resolution
1. Confirm it's actually the index and not the application by re-running the
   equivalent query with the planner forced to ignore indexes (e.g. a
   sequential scan) — if results differ, the index is the problem.
2. Rebuild the suspect index (`REINDEX` on Postgres) rather than trying to
   repair it in place — index corruption is not something to patch
   selectively.
3. Investigate why it happened before treating it as resolved — sudden power
   loss, a storage-layer fault, or a database crash during a write are the
   usual causes; a recurring pattern points at the underlying storage, not
   the database software.
4. If corruption recurs on the same volume, escalate to check the underlying
   storage/hardware rather than repeatedly reindexing the symptom.

## Notes
`REINDEX` on a large, actively-used table can be expensive and may briefly
lock it — prefer `REINDEX CONCURRENTLY` where available, and schedule
non-concurrent rebuilds for a low-traffic window.
