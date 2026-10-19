---
id: NET-FW-001
department: Networking
topic: net-firewall
title: Firewall rule needed for an application
updated: '2026-02-17'
served: true
author: R
reviewer: null
legacy: firewall-port-request
---

## Symptom
A new application or integration cannot connect to a server or external service; the
connection times out because the firewall blocks it.

## Cause
The firewall denies traffic that no rule allows. A new connection needs a rule scoped to
the exact source, destination, port and protocol.

## Resolution steps
1. Collect source IP or subnet, destination IP or host, port numbers, protocol (TCP or
   UDP) and the business reason.
2. Raise a firewall change request through the change process; rules are never added ad
   hoc, even for urgent requests.
3. When the rule is in place, test with the requester, for example with
   `Test-NetConnection <host> -Port <port>` or the application's own connection test.
4. For temporary rules (a migration), record an end date so the rule is removed.

## Warnings
Never request or approve an any-to-any rule, even temporarily.

## Key facts
- A firewall request needs source, destination, port, protocol and business reason.
- Firewall changes go through the change process, never ad hoc.
- Temporary rules must carry an end date.
- Any-to-any rules are never allowed.
