---
id: NET-DNS-002
department: Networking
topic: net-addressing
title: Connected but no internet, 169.254 address
updated: '2026-01-27'
served: true
author: R
reviewer: null
legacy: no-ip-dhcp-limited
---

## Symptom
The device connects to the network but shows "No internet" or "Limited", and
`ipconfig` shows an address starting with 169.254.

## Cause
A 169.254.x.x address is self-assigned when the device gets no reply from DHCP. One
device failing points to its cable, port or driver; many devices on the same network
point to the DHCP server or an exhausted address pool.

## Resolution steps
1. Disconnect and reconnect to trigger a new DHCP request.
2. Run `ipconfig /release` and then `ipconfig /renew`.
3. On a wired desk, try another cable and port.
4. If several devices on the same floor or network get 169.254 addresses, escalate to
   network engineering: the DHCP scope may be full or the server unreachable.

## Warnings
Do not give the device a static IP address as a fix; it can clash with addresses DHCP
hands out later.

## Key facts
- A 169.254.x.x address means the device got no answer from DHCP.
- ipconfig /release then /renew requests a fresh lease.
- Many devices with 169.254 addresses point to the DHCP server or a full scope.
