---
id: DB-CONN-003
department: Database
topic: db-connectivity
title: Password authentication failed after credential rotation
updated: '2026-09-03'
served: true
author: A
reviewer: null
---

## Symptom
An application suddenly fails with "password authentication failed for user" after a
scheduled credential rotation, while other applications work.

## Cause
The database password was rotated in the secrets manager, but this application still uses
the old password: it caches it at start-up, or reads it from a configuration file instead
of the secrets manager.

## Resolution steps
1. Confirm the failing user name and the time the errors began; compare with the rotation
   time.
2. Check how the application gets its password: secrets manager or configuration file.
3. If it uses the secrets manager but caches the value, restart the application so it
   reads the new password.
4. If it uses a configuration file, ask the owning team to switch to the secrets manager.

## Warnings
Do not reset the database password back to the old value; other applications already use
the new one.

## Key facts
- "password authentication failed" right after rotation means the application still uses the old password.
- Applications that cache secrets at start-up need a restart after rotation.
- Database passwords belong in the secrets manager, not configuration files.
