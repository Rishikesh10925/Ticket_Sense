---
id: SAP-MAT-004
department: SAP
topic: sap-materials
title: Posting period closed for goods movements
updated: '2025-09-30'
served: true
author: S
reviewer: null
---

## Symptom
A goods movement fails with a message that posting is only possible in two named
periods, for example the current and the previous month.

## Cause
The materials-management posting period only allows postings in the current and the
previous period. The period is moved forward each month with MMPV. If the month-end
change was not run, or the user picks a date in an older period, the posting is refused.

## Resolution steps
1. Check the posting date the user entered. Ask them to use a date in one of the two
   periods named in the message, if that matches when the movement really happened.
2. If the current calendar month is not among the allowed periods, the period was not
   moved forward. Check the current period with MMRV.
3. Escalate a missing period change to the materials-management team, who run MMPV.
4. Postings into an older closed period need Finance approval and are handled by
   Finance, not the helpdesk.

## Warnings
Never post with a false date to get around a closed period; it distorts stock values in
the wrong month.

## Key facts
- Materials management allows postings only in the current and previous period.
- MMRV displays the current period; MMPV moves it forward.
- Postings into older closed periods need Finance approval.
