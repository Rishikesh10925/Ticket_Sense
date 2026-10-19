---
id: SAP-INT-003
department: SAP
topic: sap-interfaces
title: Interface fails with RFC connection error
updated: '2026-07-14'
served: true
author: S
reviewer: null
---

## Symptom
An interface or background job that calls another system fails with an RFC
communication error, or a connection test for the destination fails.

## Cause
The RFC destination points to a system that is down, has moved, or rejects the stored
technical user (locked or expired password).

## Resolution steps
1. Find the RFC destination named in the error.
2. Run the connection test for it in SM59 and note the result.
3. If the test fails with a logon error, check whether the technical user in the target
   system is locked or its password expired; Basis fixes it.
4. If the target cannot be reached, check whether the target system is up and whether its
   host name changed.
5. After the fix, reprocess the failed messages or rerun the job.

## Warnings
Do not change RFC destinations in production yourself; Basis owns them.

## Key facts
- RFC destinations are tested in SM59.
- A logon failure in the test points to a locked or expired technical user.
- RFC destinations in production are changed only by Basis.
