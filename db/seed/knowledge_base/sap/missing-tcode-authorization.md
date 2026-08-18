# Missing Authorization for Transaction Code

**Department:** SAP

## Issue
User attempts to run a transaction and receives "You are not authorized to
use transaction XXXX" or a similar authorization-object error.

## Resolution
1. Ask the user for the exact transaction code and the error's authorization
   object (visible via System → Status, or in the short dump if one occurred).
2. Confirm with the user's manager that the access is appropriate for their
   role — new access always requires manager approval, logged in the access
   request ticket.
3. Submit a role-change request to the Basis/security team referencing the
   transaction code and business justification.
4. Once the role is assigned, the user must log out and back in for the new
   authorization to take effect.

## Notes
The helpdesk does not grant SAP authorizations directly — this article
covers triage and the request path only.
