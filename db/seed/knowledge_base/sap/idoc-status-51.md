# IDoc Stuck in Status 51

**Department:** SAP

## Issue
An inbound or outbound IDoc (WE02/WE05) shows status **51 — "Error: Application
document not posted"**, and the expected downstream document (order, delivery,
invoice) was never created.

## Resolution
1. Open the IDoc in WE02 and check the status record's error message — this
   usually names the exact field or missing master data causing the failure.
2. Common causes: missing customer/vendor master record, missing pricing
   condition, or a partner profile mismatch.
3. Once the underlying master data or configuration issue is fixed, reprocess
   the IDoc via BD87.
4. If the IDoc is part of a high-volume interface (EDI), check whether other
   IDocs from the same partner are also failing — a batch failure usually
   points to a partner profile or mapping change rather than one bad record.

## Notes
Do not reprocess an IDoc more than once without reading the error segment —
resubmitting a bad IDoc repeatedly can create duplicate postings if the
underlying issue was intermittent rather than a genuine data error.
