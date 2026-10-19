---
id: DB-CHG-004
department: Database
topic: db-change
title: Read-only access for reporting tools
updated: '2024-12-03'
served: true
author: A
reviewer: null
---

## Symptom
An analyst asks to connect a reporting or BI tool directly to a production database.

## Cause
Heavy reporting queries on the primary database slow down the applications that use it.
Reporting is served from a read replica with a read-only role.

## Resolution steps
1. Confirm which data the analyst needs and the manager's approval.
2. Grant the reporting read-only role on the read replica, not on the primary.
3. Give the analyst the replica's connection details and explain that data may lag a few
   seconds.
4. For personal data, check with the data protection officer before granting access.

## Warnings
Reporting tools never connect to the primary database.

## Key facts
- Reporting tools connect to the read replica, not the primary.
- Analysts get the read-only reporting role.
- Access to personal data needs the data protection officer's check.
