---
id: NET-VPN-003
department: Networking
topic: net-vpn
title: VPN connected but internal sites do not open
updated: '2026-09-08'
served: true
author: R
reviewer: null
---

## Symptom
The VPN client says it is connected, but internal websites, file shares and SAP do not
open. Public websites still work.

## Cause
The VPN tunnel is up but the laptop is not using the internal DNS servers pushed by the
VPN, or a home router uses the same private address range as an internal network, so
traffic for that range never enters the tunnel.

## Resolution steps
1. Ask the user to try an internal resource by IP address. If the IP works but the name
   does not, it is a DNS problem.
2. Run `ipconfig /all` and check that the VPN adapter lists the internal DNS servers.
3. Disconnect and reconnect the VPN; if DNS is still wrong, reinstall the VPN profile from
   the software centre.
4. If even IP addresses fail, compare the home network's address range with the internal
   ranges (for example both using 192.168.1.x). Ask the user to restart the home router
   or test from a hotspot, and report the overlap to network engineering.

## Warnings
Do not ask users to edit their hosts file for internal names; entries go stale and
break later.

## Key facts
- Reaching a resource by IP but not by name over VPN is a DNS problem.
- The VPN adapter should list the internal DNS servers in ipconfig /all.
- A home network using the same private range as an internal network stops that traffic entering the tunnel.
