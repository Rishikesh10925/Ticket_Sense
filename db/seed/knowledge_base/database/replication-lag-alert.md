# Replica Lag Past the Alert Threshold

**Department:** Database

## Issue
Monitoring fires an alert that a read replica's replication lag has exceeded
the configured threshold, or an application reading from a replica reports
seeing stale data.

## Resolution
1. Check the primary's write volume around the time lag started — a burst of
   heavy writes (bulk import, large batch update) is the most common cause
   and is usually self-resolving once the burst ends.
2. Check the replica's own resource usage (CPU, disk I/O) — a replica that's
   under-provisioned for the write volume it needs to replay will lag
   persistently, not just during bursts.
3. Check for a long-running query on the replica itself — on some replication
   setups a long read transaction on the replica can block replay of
   incoming changes.
4. If lag is sustained and not explained by a write burst, escalate rather
   than waiting it out — persistent lag risks the replica falling far enough
   behind that catching up requires a full re-sync.

## Notes
Any application relying on a replica for reads must tolerate some lag by
design — if a specific feature genuinely needs read-your-writes consistency,
route that specific read to the primary rather than trying to eliminate lag
entirely.
