---
id: CLD-STO-001
department: Cloud
topic: cloud-storage
title: Access denied on an object storage bucket
updated: '2026-07-21'
served: true
author: R
reviewer: null
legacy: s3-access-denied
---

## Symptom
An application or user gets "Access Denied" when reading or writing objects in a storage
bucket they expect to use.

## Cause
"Access Denied" is deliberately generic. The block can come from the caller's identity
policy, the bucket policy (for example a condition on network or VPC endpoint), or an
explicit deny anywhere, which always overrides any allow.

## Resolution steps
1. Get the exact bucket, object key or prefix, and the action that failed (read, write or
   list).
2. Check the caller's policies for an explicit deny on that action.
3. Check the bucket policy for conditions that block the caller, such as a required VPC
   endpoint or source IP.
4. If the caller lacks list permission, a missing object can look like access denied. Do
   not assume the object is gone until access is confirmed.
5. Request the missing permission through the normal access process.

## Warnings
Never make a bucket public to fix an access-denied error.

## Key facts
- An explicit deny always overrides an allow.
- Bucket policies can block a correctly permissioned caller through conditions.
- Without list permission, a missing object can return access denied.
