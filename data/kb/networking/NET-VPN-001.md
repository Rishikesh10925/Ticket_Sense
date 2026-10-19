---
id: NET-VPN-001
department: Networking
topic: net-vpn
title: VPN client not connecting
updated: '2026-05-02'
served: true
author: R
reviewer: null
legacy: vpn-not-connecting
---

## Symptom
The VPN client hangs at "Connecting...", or fails at once with an authentication or
timeout error. Internet access without the VPN works.

## Cause
Usually one of: the local network blocks the VPN (hotel, airport or public Wi-Fi), the
user's domain account is locked or its password expired, the VPN adapter was disabled by
an update, or the VPN gateway itself is down.

## Resolution steps
1. Confirm the internet works without the VPN by loading any public website.
2. Ask whether colleagues can connect. If several users fail at the same time, check the
   gateway status and escalate to network engineering instead of fixing clients one by one.
3. If the error mentions authentication, check whether the domain account is locked or
   the password has expired, and fix that first.
4. If the client hangs at "Connecting" with no login prompt, ask the user to retry from a
   mobile hotspot. If that works, the original network blocks the VPN.
5. If the VPN network adapter shows as disabled after a Windows update, restart the
   machine, then reinstall the VPN client from the software centre if it is still missing.

## Warnings
Do not ask the user to turn off the Windows firewall or antivirus to test the VPN.

## Key facts
- A hang at "Connecting" with no login prompt points to a network that blocks the VPN.
- A mobile hotspot test separates a blocking network from a client fault.
- Authentication errors are checked against a locked or expired domain account first.
- Many users failing at once means a gateway problem for network engineering.
