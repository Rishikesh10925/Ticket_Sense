---
id: SAP-ACC-004
department: SAP
topic: sap-access
title: Fiori app tile missing from the launchpad
updated: '2025-11-18'
served: true
author: S
reviewer: Claude
---

## Symptom
A Fiori app the user needs does not appear on their Fiori launchpad, even though a
colleague with the same job can see it. Searching the app finder does not show it either.

## Cause
Tiles come from business catalogs and groups assigned through PFCG roles. Either the
role with the catalog is missing, or it was assigned recently and the launchpad is still
showing cached content.

## Resolution steps
1. Ask the user for the exact app name and a colleague who can see it.
2. Ask the user to sign out of the launchpad, clear the browser cache and sign in again.
   A role assigned in the last hour often appears after this.
3. If it is still missing, compare the user's roles with the colleague's in SU01 (Roles
   tab) and note the role that carries the app's catalog.
4. Request that role through the normal access process with manager approval, as for
   any new SAP access.

## Warnings
Copying all of a colleague's roles is not allowed: request only the role that carries
the missing app.

## Key facts
- Fiori tiles come from business catalogs assigned through PFCG roles.
- A newly assigned role may only appear after signing out and clearing the browser cache.
- Missing roles are requested through the access process with manager approval, never copied wholesale from a colleague.
