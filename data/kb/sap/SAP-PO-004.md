---
id: SAP-PO-004
department: SAP
topic: sap-procurement
title: Vendor invoice blocked for payment
updated: '2026-03-25'
served: true
author: S
reviewer: null
---

## Symptom
A vendor says they have not been paid. The invoice was posted in MIRO but shows a
payment block, so the payment run skipped it.

## Cause
MIRO sets a payment block automatically when the invoice differs from the PO or the
goods receipt beyond the tolerances: usually a price variance, a quantity variance, or
an invoice posted before the goods receipt.

## Resolution steps
1. Ask for the vendor number and invoice number, and find the document.
2. Run MRBR (release blocked invoices) for that vendor to see why it is blocked: price,
   quantity or date variance.
3. For a quantity block caused by a missing goods receipt, ask the receiving team to post
   the receipt. The block can then be released.
4. For a price variance, the buyer must confirm the price with the vendor. If it is
   correct, accounts payable releases the invoice in MRBR.
5. Tell the vendor the invoice will be paid in the next payment run after release.

## Warnings
Only accounts payable releases blocked invoices. The helpdesk does not.

## Key facts
- MIRO blocks invoices for payment when they differ from the PO or goods receipt beyond tolerance.
- MRBR shows why an invoice is blocked and is used to release it.
- A quantity block caused by a missing goods receipt clears once the receipt is posted.
- Blocked invoices are released by accounts payable, not the helpdesk.
