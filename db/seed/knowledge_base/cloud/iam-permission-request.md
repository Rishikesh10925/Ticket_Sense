# Requesting New IAM Permissions

**Department:** Cloud

## Issue
A user or service needs additional cloud permissions (e.g., access to a new
service, resource, or action) that their current role doesn't grant.

## Resolution
1. Identify the minimum specific actions and resources needed — avoid
   requesting broad managed policies (e.g., full service admin) when a
   narrower custom policy will do.
2. Submit the request with business justification and, for service
   accounts, an owner/team responsible for the credential.
3. Permissions are granted via role/group membership, not by attaching
   policies to individual users directly — this keeps access auditable and
   revocable.
4. Time-bound or project-specific access should have a stated review/expiry
   date in the ticket.

## Notes
Requests for permanent, broad access "just in case" should be pushed back
on — scope to what's actually needed and expand later if a genuine gap
appears.
