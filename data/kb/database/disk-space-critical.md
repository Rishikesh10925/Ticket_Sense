# Database Volume Nearing or at Disk-Space Capacity

**Department:** Database

## Issue
Disk-space monitoring alerts that the database's storage volume is nearing
capacity, or the database has already started rejecting writes because the
volume is full.

## Resolution
1. Identify what's actually consuming space — table/index bloat, an
   oversized WAL/transaction log backlog (often from a replication slot that
   isn't advancing), or genuine data growth — rather than immediately
   resizing the volume without knowing why.
2. If it's a stuck replication slot holding WAL, find and fix the consumer
   that isn't advancing (a disconnected replica or a stalled logical
   replication subscriber) before it repeats.
3. If it's table/index bloat, a `VACUUM`/reindex may reclaim meaningful space
   once the immediate crisis is handled — not a first response under active
   pressure, since it adds load.
4. If space is needed immediately to restore write availability, expand the
   volume — this is the fast, safe mitigation; treat it as buying time for
   the actual root-cause investigation above, not the fix itself.

## Notes
A database that has fully run out of disk space can fail in ways that are
hard to recover from cleanly (including refusing to start) — treat "nearing
capacity" alerts as urgent, not "at capacity" alerts.
