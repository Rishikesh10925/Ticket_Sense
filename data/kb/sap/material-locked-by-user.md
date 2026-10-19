# Material Master Locked by Another User

**Department:** SAP

## Issue
Attempting to edit a material master (MM02) returns "Material XXXX is
currently locked by user YYYY".

## Resolution
1. Confirm whether the listed user actually has the material open in an edit
   session (ask them directly, or check via SM12 for the lock entry).
2. If the session is genuinely still open, ask that user to save or exit —
   this resolves the lock immediately.
3. If the user's session crashed or they're unreachable, a Basis admin can
   remove the specific lock entry via SM12 after confirming no active edit
   is in progress.
4. Never delete a lock entry without confirming the other session is truly
   dead — doing so while an edit is genuinely in progress can cause data
   loss.

## Notes
Repeated locking on the same material by the same user usually means a
previous GUI session didn't close cleanly — check for orphaned SAP GUI
processes on that user's machine.
