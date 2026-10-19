---
id: CLD-IAM-003
department: Cloud
topic: cloud-iam
title: Cloud access key exposed or committed to a repository
updated: '2026-08-30'
served: true
author: R
reviewer: null
---

## Symptom
A developer reports that a cloud access key was pushed to a code repository, pasted in a
chat, or shared in a ticket, or the security team receives an alert that a key appeared
in a public place.

## Cause
Long-lived access keys were stored in code or configuration. Anyone who sees the key can
act with its permissions until it is disabled.

## Resolution steps
1. Treat it as a security incident at once and notify the security team.
2. Deactivate the exposed key immediately in the identity console. Do not wait for the
   developer to finish their work.
3. Create a new key for the owner only if the workload still needs one, and prefer a role
   with temporary credentials instead.
4. Remove the key from the repository history, not just the latest commit. Rotating the
   key matters more than cleaning the history.
5. Ask the security team to review the account's activity logs for use of the old key.

## Warnings
Deleting the commit is not enough: a pushed key must be treated as compromised and
deactivated.

## Key facts
- An exposed access key is deactivated immediately, before anything else.
- A key that was pushed or shared is compromised even if the commit is removed.
- Roles with temporary credentials are preferred over long-lived access keys.
- Activity logs are reviewed for use of the exposed key.
