---
id: SAP-FI-003
department: SAP
topic: sap-finance
title: General ledger account blocked for posting
updated: '2025-06-17'
served: false
author: S
reviewer: null
---

## Symptom
A posting fails because a general ledger account is blocked for posting.

## Cause
Finance blocks G/L accounts that are being retired or restructured. The block is set in
the account master (FS00).

## Resolution steps
1. Note the G/L account and company code from the message.
2. Ask the user which business transaction they were posting.
3. Ask the Finance master-data team which account replaces the blocked one.
4. The user posts to the replacement account.

## Warnings
Do not ask for a blocked account to be unblocked to post one document; use the
replacement account.

## Key facts
- G/L accounts are blocked for posting in the account master (FS00).
- Blocked accounts usually have a replacement account named by Finance master data.
- Postings go to the replacement account rather than unblocking the old one.
