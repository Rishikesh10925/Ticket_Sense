# Requesting Read/Write Access to a Schema or Table

**Department:** Database

## Issue
A developer or service needs read or write access to a specific database,
schema, or table that they don't currently have permissions for.

## Resolution
1. Confirm the exact scope needed — a specific table, a whole schema, or the
   whole database — and whether read-only or read/write, rather than
   granting broader access than requested "to be safe."
2. Grant the narrowest role/privilege that satisfies the request (e.g. a
   read-only role scoped to the one schema) rather than adding the requester
   directly to a broad admin role.
3. For a service account (not a human), prefer a dedicated role per service
   over reusing an existing one — this keeps access auditable and revocable
   per-service later.
4. Record the grant (who, what, why, when) somewhere reviewable — access
   requests without a record are the reason access audits take so long.

## Notes
Time-bound access (revisit/revoke after a project ends) is preferable to
permanent grants for anything beyond a service's standing operational needs,
even though nothing in this project automates that yet.
