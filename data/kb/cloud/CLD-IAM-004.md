---
id: CLD-IAM-004
department: Cloud
topic: cloud-iam
title: Lost phone for cloud console multi-factor sign-in
updated: '2025-04-17'
served: true
author: R
reviewer: null
---

## Symptom
The user has a new or lost phone and can no longer complete the multi-factor step when
signing in to the cloud console.

## Cause
Multi-factor for the console runs through the corporate identity provider. The
authenticator was registered on the old phone.

## Resolution steps
1. Verify the user's identity through the standard process (manager confirmation plus
   employee ID).
2. Ask the identity team to reset the user's multi-factor registration in the identity
   provider.
3. The user registers the authenticator on the new phone at the next sign-in.
4. If the phone was lost, ask the user to report it to security as a lost device.

## Warnings
Never turn multi-factor off for an account, even temporarily.

## Key facts
- Console multi-factor is managed in the corporate identity provider.
- A multi-factor reset needs identity verification first.
- A lost phone is also reported to security as a lost device.
