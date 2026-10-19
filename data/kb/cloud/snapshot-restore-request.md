# Requesting a Snapshot/Backup Restore

**Department:** Cloud

## Issue
A resource (volume, database, VM) needs to be restored from a snapshot or
backup due to accidental deletion, corruption, or a needed rollback.

## Resolution
1. Confirm the exact resource, the target point in time, and why the restore
   is needed — this affects whether a full restore or a point-in-time
   restore to a new resource is more appropriate.
2. Restoring to a **new** resource (rather than overwriting the original) is
   the default safe approach — this avoids permanently losing current state
   if the restore turns out to be the wrong one.
3. Confirm downstream dependents (DNS records, connection strings, other
   services pointing at this resource) before cutting over to the restored
   copy.
4. Document the restore in the ticket, including the snapshot/backup
   timestamp used, for audit purposes.

## Notes
Never delete the original resource before confirming the restored copy is
verified and working.
