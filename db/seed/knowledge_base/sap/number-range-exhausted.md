# Number Range Interval Exhausted

**Department:** SAP

## Issue
Creating a new document (sales order, material, PO) fails with "Number range
interval XX not found" or "No more numbers available".

## Resolution
1. Identify the number range object from the error message (e.g., document
   type's number range in VN01/SNRO depending on object type).
2. Check the current interval's "To number" against the "current number" —
   if exhausted, a Basis/config admin needs to extend the interval or add a
   new one.
3. This is a configuration change, not something the helpdesk can fix
   directly — escalate with the exact number range object and document
   type affected.
4. Flag to the process owner that this will recur unless the interval is
   extended generously (not just by a small buffer).

## Notes
Number range exhaustion tends to happen right before a fiscal year-end
close — check whether year-end number range maintenance was missed.
