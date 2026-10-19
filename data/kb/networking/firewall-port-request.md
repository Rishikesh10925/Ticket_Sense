# Requesting a New Firewall Port Rule

**Department:** Networking

## Issue
An application or integration fails to connect because traffic is being
blocked by the corporate firewall, and a new rule is needed.

## Resolution
1. Gather the required details before submitting: source IP/subnet,
   destination IP/subnet, port(s), protocol (TCP/UDP), and business
   justification.
2. Submit the request through the standard change process — firewall
   changes require approval and are not made ad hoc, even for urgent
   requests.
3. Test the new rule with the requester once implemented (e.g., `telnet
   <host> <port>` or the application's own connectivity test) before
   closing the ticket.
4. Time-bound or temporary rules (e.g., for a migration) should be flagged
   for removal with an explicit end date.

## Notes
Never request or approve a "temporary" wide-open rule (e.g., any-any) —
scope every rule to the specific IPs and ports actually needed.
