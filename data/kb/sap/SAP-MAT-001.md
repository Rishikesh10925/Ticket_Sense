---
id: SAP-MAT-001
department: SAP
topic: sap-materials
title: Material master locked by another user
updated: '2026-07-07'
served: true
author: S
reviewer: Claude
legacy: material-locked-by-user
---

## Symptom
Changing a material in MM02 fails with a message that the material is currently being
processed by another user, who is named in the message.

## Cause
SAP sets a lock entry while someone edits a material. The lock is released when they
save or leave the transaction. If their session crashed, the lock can be left behind.

## Resolution steps
1. Contact the named user and ask them to save or exit MM02. This releases the lock at once.
2. If they are unreachable or say they are not editing, check SM12 for the lock entry on
   the material and note the user and the time it was created.
3. A Basis administrator confirms the user has no active session (SM04) before deleting
   the lock entry in SM12.
4. Ask the original requester to retry MM02.

## Warnings
Deleting a lock entry while the other user is still editing can corrupt the material
data. Only Basis deletes lock entries, and only after confirming the session is gone.

## Key facts
- A material is locked while another user edits it in MM02.
- Lock entries are listed in SM12.
- Basis deletes a lock entry only after confirming in SM04 that the session is gone.
