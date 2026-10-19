---
id: CLD-STO-002
department: Cloud
topic: cloud-storage
title: Writes fail because a storage quota is reached
updated: '2026-02-24'
served: true
author: R
reviewer: null
legacy: storage-quota-exceeded
---

## Symptom
An application or backup job fails with a quota or limit error, or writes start failing
while reads still work.

## Cause
A limit was reached: an account-level service quota, a size limit on a volume or file
share, or a budget control that stops further spending.

## Resolution steps
1. Read the error to identify which limit was hit.
2. Check whether old data can be archived or deleted under the retention policy before
   asking for more space.
3. Request a service quota increase through the cloud provider's process. It is not
   instant, so state clearly if production is blocked.
4. If usage grows steadily, raise a capacity-planning review instead of repeated small
   increases.

## Warnings
Do not request the largest possible quota "to be safe"; it hides runaway growth.

## Key facts
- Quota errors can come from service quotas, size limits or budget controls.
- Retention-policy clean-up is checked before requesting more capacity.
- Service quota increases are not instant.
