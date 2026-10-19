---
id: CLD-STO-003
department: Cloud
topic: cloud-storage
title: How long files are kept in a bucket
updated: '2025-09-16'
served: true
author: R
reviewer: null
legacy: lifecycle-policy-retention
---

## Symptom
A user asks how long objects in a bucket are kept, why old files moved to archive or
disappeared, or wants the retention changed.

## Cause
Lifecycle rules on the bucket move objects to cheaper storage classes or delete them
after a set number of days.

## Resolution steps
1. Check the bucket's lifecycle rules for transition and expiration settings.
2. Explain the current rule to the user in plain terms (for example "archived after 90
   days, deleted after 3 years").
3. For a change, confirm with the data owner, and with compliance if the bucket holds
   business records.
4. Note that rule changes apply going forward: objects already deleted under the old rule
   are not restored.

## Warnings
Never shorten retention on a bucket under legal or compliance hold.

## Key facts
- Lifecycle rules transition or delete objects after a number of days.
- Retention changes need the data owner's approval, and compliance for business records.
- Lifecycle rule changes do not restore objects already deleted.
