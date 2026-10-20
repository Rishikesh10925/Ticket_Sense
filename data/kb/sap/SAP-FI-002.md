---
id: SAP-FI-002
department: SAP
topic: sap-finance
title: Posting period not open in finance
updated: '2026-09-30'
served: false
author: S
reviewer: Claude
---

## Symptom
A finance posting fails with a message that the posting period is not open for the
account type.

## Cause
Finance posting periods are opened and closed per account type in OB52 during month-end
close. Postings into a closed period are rejected.

## Resolution steps
1. Note the posting date, company code and account type in the message.
2. Check whether the date is correct; a typing error in the year is common.
3. If the date is right and the period should be open, ask the Finance close team; they
   open periods in OB52.
4. Postings into a period that Finance has closed for good need Finance approval.

## Warnings
Do not open posting periods yourself; period control is a Finance task.

## Key facts
- Finance posting periods are controlled per account type in OB52.
- Postings into a closed period are rejected.
- Only the Finance close team opens or closes periods.
