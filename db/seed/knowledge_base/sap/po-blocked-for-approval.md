# Purchase Order Blocked for Release (ME21N)

**Department:** SAP

## Issue
A newly created purchase order shows "Release Strategy" active in ME21N/
ME22N and cannot be sent to the vendor or receipted against.

## Resolution
1. Check the **Release Strategy** tab on the PO — this shows which approval
   level(s) are still outstanding.
2. Confirm with the requester who the current approver is (based on PO value
   and the configured release hierarchy) and whether they've been notified.
3. Approvers release POs via ME28 (individual or collective release), not by
   editing the PO directly.
4. If an approver is out of office, their manager or a designated backup
   approver (configured per release strategy) can release on their behalf.

## Notes
The helpdesk cannot release a PO on behalf of an approver — only escalate to
confirm the correct approver is aware.
