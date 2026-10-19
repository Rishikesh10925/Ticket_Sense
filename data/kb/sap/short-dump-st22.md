# Short Dump (ST22) Troubleshooting

**Department:** SAP

## Issue
A user's transaction ends abruptly with a generic error screen ("An
exception occurred") instead of completing normally.

## Resolution
1. Ask the user for the approximate time and transaction code, then look it
   up in ST22 (Dump Analysis).
2. Read the dump's "Error Analysis" section — common runtime errors include
   `TIME_OUT` (long-running report exceeded the time limit),
   `DBIF_RSQL_SQL_ERROR` (database issue), and `CONVT_NO_NUMBER` (bad input
   data).
3. `TIME_OUT` dumps on reports usually mean the selection criteria was too
   broad — ask the user to narrow the date range or filters and retry.
4. Dumps pointing to a custom program (Z-program) should be routed to the
   development team with the dump ID, not resolved by the helpdesk.

## Notes
Always capture the dump ID (top of the ST22 screen) before escalating —
developers need it to pull the exact runtime context.
