---
id: SAP-PO-002
department: SAP
topic: sap-procurement
title: Purchase order waiting for release
updated: '2026-06-14'
served: true
author: S
reviewer: null
legacy: po-blocked-for-approval
---

## Symptom
A new purchase order cannot be printed or sent to the vendor, and goods cannot be
received against it. ME23N shows a release strategy on the PO header.

## Cause
POs above a value limit go through a release strategy. Until every required approver has
released it, the PO stays blocked for output and follow-on documents.

## Resolution steps
1. Open the PO in ME23N and go to the Release Strategy tab in the header. It lists each
   release code and shows which are still outstanding.
2. Tell the requester who the outstanding approver is and ask them to follow up.
3. Approvers release individual POs in ME29N or several at once in ME28. Editing the PO
   is not a release.
4. If the approver is away, the deputy configured for that release code can release on
   their behalf.

## Warnings
The helpdesk cannot release a PO for an approver. Changing the PO value to get under the
release limit is a policy violation.

## Key facts
- The Release Strategy tab in ME23N shows which approvals are outstanding.
- Approvers release POs in ME29N (individually) or ME28 (collectively).
- A deputy configured for the release code can release when the approver is absent.
- The helpdesk never releases a PO on an approver's behalf.
