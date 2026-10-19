---
id: CLD-IAM-002
department: Cloud
topic: cloud-iam
title: Single sign-on to the cloud console fails
updated: '2026-09-14'
served: true
author: R
reviewer: null
legacy: sso-console-login-failure
---

## Symptom
The user cannot sign in to the cloud console through single sign-on: they are sent back to
the login page, see an identity-provider error, or land on an empty console with access
denied.

## Cause
The corporate account is locked or disabled, the user is not assigned to the cloud
application in the identity provider, or they are assigned but no role or permission set
is mapped to their group.

## Resolution steps
1. Ask whether other single sign-on apps work. If they all fail, it is an account problem
   in the identity provider, not a cloud problem.
2. Check that the user is assigned to the cloud console application in the identity
   provider. A missing assignment causes a redirect loop.
3. If sign-in works but the console is empty or denies everything, check which groups map
   to which cloud roles, and request the right group.
4. Ask the user to retry in a private browser window to rule out a stale session.
5. If many users fail at once, treat it as a single sign-on outage and escalate.

## Warnings
Do not create a local cloud user with a password as a workaround for single sign-on.

## Key facts
- If all single sign-on apps fail, the problem is the corporate account, not the cloud.
- A user not assigned to the cloud app in the identity provider gets a redirect loop.
- Signing in but seeing access denied means no role is mapped to the user's groups.
