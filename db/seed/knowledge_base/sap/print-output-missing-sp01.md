# Print Output Not Appearing in SP01

**Department:** SAP

## Issue
A document was printed (invoice, PO, delivery note) but nothing shows up in
the print queue or at the printer.

## Resolution
1. Check SP01 (Output Controller) for the spool request — filter by user and
   creation date/time.
2. If the spool request exists but shows an error status, open it and check
   the error message — most common cause is the output device not being
   assigned to the printer that's actually online.
3. If no spool request was created at all, the print wasn't triggered from
   SAP — check the print program/output type configuration for that
   document type.
4. To resend a spool request that exists but never reached the printer, use
   SP01 → select request → Print.

## Notes
Printer hardware issues (offline, out of paper, driver errors) are a
Networking/desktop-support matter, not an SAP configuration issue.
