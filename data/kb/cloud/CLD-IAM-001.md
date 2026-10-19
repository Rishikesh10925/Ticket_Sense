---
id: CLD-IAM-001
department: Cloud
topic: cloud-iam
title: Request for additional cloud permissions
updated: '2026-06-09'
served: true
author: R
reviewer: null
legacy: iam-permission-request
---

## Symptom
A user or a service account gets "not authorized to perform" errors for a cloud action
and asks for more permissions.

## Cause
The identity's roles do not include the action on that resource. New projects and new
services often need permissions nobody requested yet.

## Resolution steps
1. Get the exact error: it names the action (for example `s3:PutObject`) and the resource.
2. Ask for the business reason, and for service accounts, the owning team.
3. Request the narrowest permission: the specific actions on the specific resources, not a
   broad managed policy such as full admin for the service.
4. Permissions are granted through group or role membership, never by attaching a policy
   to an individual user.
5. For project or temporary access, record a review or expiry date in the ticket.

## Warnings
Push back on "just give full access to be safe". Broad standing permissions are the most
common cause of cloud security incidents.

## Key facts
- The authorization error names the denied action and resource.
- Permissions are granted through groups or roles, not policies on individual users.
- Requests are scoped to specific actions and resources (least privilege).
- Temporary access carries an expiry or review date.
