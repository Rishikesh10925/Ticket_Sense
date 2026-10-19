---
id: SAP-ACC-001
department: SAP
topic: sap-access
title: SAP user account locked
updated: '2026-08-11'
served: true
author: S
reviewer: null
legacy: locked-user-account
---

## Symptom
The user cannot log on to SAP GUI or Fiori. The logon screen reports that the user is
locked, usually after several failed password attempts.

## Cause
SAP locks a user after too many failed logons. The limit is the profile parameter
`login/fails_to_user_lock`, set to 5 in this organisation. An administrator can also
lock a user on purpose, for example after a security incident or when someone leaves.

## Resolution steps
1. Verify the caller's identity: employee ID plus confirmation from their manager for
   phone or chat requests.
2. Open SU01 for the user and check the lock status on the Logon Data tab. "Locked by
   incorrect logon" can be unlocked by the helpdesk. "Locked by administrator" cannot.
3. For a failed-logon lock, unlock the user in SU01 (Lock/Unlock) and set a new initial
   password with Change Password.
4. Give the initial password to the user through the approved channel only. SAP forces
   them to choose a new password at the next logon.
5. If the user is locked by an administrator, do not unlock. Escalate to the SAP security
   team with the user ID.

## Warnings
Never unlock an account locked by an administrator. Never send an initial password to an
address that has not been verified.

## Key facts
- The failed-logon limit is set by login/fails_to_user_lock (5 here).
- Only failed-logon locks may be removed by the helpdesk; administrator locks are escalated to SAP security.
- Unlocking and setting an initial password are both done in SU01.
- An initial password must be changed by the user at the next logon.
