---
id: DB-CHG-003
department: Database
topic: db-change
title: Request to run a data fix in production
updated: '2026-08-08'
served: true
author: A
reviewer: null
---

## Symptom
A team asks the DBA team to run an `UPDATE` or `DELETE` script in production to correct
bad data.

## Cause
Application bugs or bad imports leave wrong data that the application cannot correct
itself.

## Resolution steps
1. Require the script, the expected number of affected rows and an approved change request.
2. Run the script's `WHERE` clause as a `SELECT COUNT(*)` first and compare with the
   expected number.
3. Take a backup of the affected rows (or an on-demand backup) before running it.
4. Run the script in a transaction, check the row count reported, and only then commit.

## Warnings
Never run a data fix that has no `WHERE` clause or whose row count does not match the
expected number.

## Key facts
- Production data fixes need an approved change and the expected row count.
- The WHERE clause is tested with SELECT COUNT(*) before the change runs.
- Data fixes run inside a transaction and are committed only if the row count matches.
