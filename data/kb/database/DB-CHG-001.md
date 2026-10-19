---
id: DB-CHG-001
department: Database
topic: db-change
title: Request for access to a database
updated: '2026-05-04'
served: true
author: A
reviewer: null
legacy: db-access-permission-request
---

## Symptom
A developer or a service asks for read or write access to a database, schema or table.

## Cause
Access is granted per role. A new project or service often needs access that nobody has
requested yet.

## Resolution steps
1. Confirm the exact scope (table, schema or database) and whether read-only or read-write.
2. Get the manager's approval and the business reason.
3. Grant the narrowest existing role that fits, for example the schema's read-only role.
   For a service, create a dedicated role for that service.
4. Record who, what, why and when in the ticket, and an end date for temporary access.

## Warnings
Never add a person to the database owner or superuser role to grant access.

## Key facts
- Access is granted through the narrowest role that fits the request.
- Each service gets its own dedicated role.
- Grants are recorded with who, what, why and when.
