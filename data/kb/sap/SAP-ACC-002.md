---
id: SAP-ACC-002
department: SAP
topic: sap-access
title: Not authorised for a transaction
updated: '2026-05-20'
served: true
author: S
reviewer: null
legacy: missing-tcode-authorization
---

## Symptom
Starting a transaction fails with "You are not authorized to use transaction XXXX", or
an action inside a transaction fails with a missing-authorization message.

## Cause
The user's roles do not contain the authorization object and values that the
transaction checks. This often happens after a job change, or when a new transaction is
rolled out without a matching role.

## Resolution steps
1. Ask the user to reproduce the error and then immediately run transaction SU53. It
   shows the last failed authorization check: the object, field and value that were missing.
2. Ask for a screenshot of SU53 and the transaction code.
3. Confirm with the user's manager that the access fits the user's job. New access always
   needs manager approval, recorded in the access-request ticket.
4. Raise a role-change request to the SAP security team with the SU53 screenshot, the
   transaction code and the business justification.
5. When the role is assigned, ask the user to log off and log on again so the new
   authorizations are loaded.

## Warnings
The helpdesk never assigns SAP roles itself and never grants SAP_ALL or similar broad
profiles as a workaround.

## Key facts
- SU53 shows the last failed authorization check for the current user.
- New SAP access always needs manager approval recorded in the request.
- Role changes are made by the SAP security team, not the helpdesk.
- The user must log on again before a newly assigned role takes effect.
