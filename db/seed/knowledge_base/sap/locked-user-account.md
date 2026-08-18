# SAP User Account Locked

**Department:** SAP

## Issue
User cannot log into SAP GUI or Fiori; system shows "User is locked" or the
password field is greyed out after repeated failed logins.

## Resolution
1. Confirm the user's identity (employee ID + manager confirmation for phone
   requests).
2. In SU01, check the **Lock** tab — accounts lock automatically after 5
   failed password attempts within a rolling 24-hour window.
3. Unlock via SU01 → Lock/Unlock System, then trigger a password reset email
   from the same screen.
4. Ask the user to log in within 24 hours; unused reset links expire.

## Notes
Repeated lockouts within the same week usually indicate a saved password in
a script or scheduled task using stale credentials — check for background
jobs running under the user's ID.
