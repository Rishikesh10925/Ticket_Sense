---
id: NET-DNS-003
department: Networking
topic: net-addressing
title: Windows reports an IP address conflict
updated: '2025-08-12'
served: true
author: R
reviewer: null
---

## Symptom
Windows shows "Windows has detected an IP address conflict" and the connection becomes
unreliable or drops.

## Cause
Two devices are using the same IP address, almost always because one of them (a printer,
a test machine) was given a static address inside the DHCP range.

## Resolution steps
1. Run `ipconfig /release` and `ipconfig /renew` on the user's laptop to get a new
   address; this usually restores the connection at once.
2. Note the conflicting address from the message or the event log.
3. Report the address to network engineering so they can find the device with the static
   address and either reserve it or move it outside the DHCP range.

## Warnings
Do not set a static address on the laptop to escape the conflict; it only moves the
problem.

## Key facts
- IP conflicts are usually caused by a static address inside the DHCP range.
- Renewing the DHCP lease gives the laptop a new address and restores the connection.
- The device with the static address must be reserved or moved outside the DHCP range.
