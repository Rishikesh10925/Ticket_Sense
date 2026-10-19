---
id: SAP-SYS-002
department: SAP
topic: sap-system
title: Short dump during a transaction
updated: '2025-05-08'
served: true
author: S
reviewer: null
legacy: short-dump-st22
---

## Symptom
A transaction ends suddenly with a runtime error screen instead of completing.

## Cause
An ABAP program hit a runtime error (a short dump). Common ones are TIME_OUT (a dialog
step ran longer than allowed), DBIF_RSQL_SQL_ERROR (a database error) and
CONVT_NO_NUMBER (text where a number was expected, usually bad input).

## Resolution steps
1. Ask the user for the transaction code and the approximate time of the error.
2. Find the dump in ST22 for that user and time, and read the runtime error name and
   the "What happened" and "Error analysis" sections.
3. For TIME_OUT on a report, ask the user to narrow the selection (shorter date range,
   fewer items) or run the report in the background.
4. For CONVT_NO_NUMBER, check the input the user typed for letters or separators in a
   numeric field.
5. For dumps in custom programs (names starting with Z or Y), send the dump to the
   development team.

## Warnings
Always record the dump date, time and user before escalating. Dumps are deleted
automatically after a retention period.

## Key facts
- ST22 lists short dumps by user and time.
- TIME_OUT means a dialog step exceeded the allowed runtime; narrowing the selection or running in background avoids it.
- Dumps in custom Z or Y programs go to the development team.
