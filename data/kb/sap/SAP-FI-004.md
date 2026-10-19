---
id: SAP-FI-004
department: SAP
topic: sap-finance
title: Vendor not included in the payment run
updated: '2024-06-11'
served: false
author: S
reviewer: null
---

## Symptom
A vendor invoice that is due was not paid in the automatic payment run.

## Cause
The payment run (F110) only pays open items that are due by the next run date, are not
blocked for payment, and whose vendor has a valid bank account and payment method.

## Resolution steps
1. Check the invoice in the vendor line items for a payment block.
2. Check the due date against the payment run's next run date.
3. Check the vendor master for a payment method and valid bank details.
4. Ask accounts payable to review the payment run's exception list, which explains each
   item that was not paid.

## Warnings
Do not change vendor bank details from a request by email; it is a common fraud pattern
and goes through vendor master verification.

## Key facts
- The automatic payment run is F110.
- Items are paid only if due, not blocked, and the vendor has a payment method and bank details.
- The payment run exception list explains why items were not paid.
