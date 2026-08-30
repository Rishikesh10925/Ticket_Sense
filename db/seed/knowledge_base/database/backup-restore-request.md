# Requesting a Database Backup or Point-in-Time Restore

**Department:** Database

## Issue
A team needs either a fresh backup taken before a risky change, or a restore
of a database/table to a point before accidental data loss (bad migration,
mistaken `DELETE`/`UPDATE` without a `WHERE` clause, etc.).

## Resolution
1. For a pre-change backup: confirm the target database and the retention
   window needed, then trigger an on-demand backup rather than relying on the
   next scheduled one — the requester should get a backup ID/timestamp back
   to confirm it succeeded before proceeding with their change.
2. For a restore: get the exact time the bad change happened (from
   application logs or the requester's own timeline) so the restore point can
   be set just before it, minimizing data loss between the restore point and
   now.
3. Restore to a **new** instance/database first, never in place over the live
   one — this lets the requester verify the restored data is correct before
   any cutover, and keeps the live database available throughout.
4. Once verified, coordinate the cutover (or selective data copy from the
   restored copy back into production) with the requester directly, since
   this often needs an application-level maintenance window.

## Notes
Never restore in place without a verified-good copy first — an unverified
restore that turns out wrong compounds the original data loss with downtime.
