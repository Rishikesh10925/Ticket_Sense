---
id: SAP-INT-002
department: SAP
topic: sap-interfaces
title: IDoc in status 51
updated: '2026-01-12'
served: true
author: S
reviewer: null
legacy: idoc-status-51
---

## Symptom
An inbound IDoc shows status 51, "Application document not posted", in WE02 or WE05,
and the expected order, delivery or invoice was never created.

## Cause
The IDoc arrived but the application could not post it. Typical reasons are missing
master data (customer, vendor or material), a missing pricing condition, or a partner
profile mismatch.

## Resolution steps
1. Open the IDoc in WE02 and read the status record for status 51. The error message
   usually names the missing field or master record.
2. Fix the cause, or ask the master-data team to create the missing record.
3. Reprocess the IDoc with BD87.
4. If many IDocs from the same partner fail at once, check the partner profile and any
   recent mapping change instead of fixing IDocs one by one.

## Warnings
Do not reprocess an IDoc repeatedly without reading the error. If the cause was
intermittent, repeated attempts can create duplicate documents.

## Key facts
- Status 51 means the application document was not posted.
- The status record in WE02 names the reason for the failure.
- Failed IDocs are reprocessed with BD87 after the cause is fixed.
- Many failures from one partner point to the partner profile or mapping.
