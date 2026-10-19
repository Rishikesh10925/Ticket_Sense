---
id: NET-PERF-001
department: Networking
topic: net-performance
title: Video calls freeze or lag
updated: '2026-07-31'
served: true
author: R
reviewer: null
legacy: video-call-latency
---

## Symptom
Video and audio calls freeze, drop or lag, while web browsing seems normal.

## Cause
Calls need low latency more than bandwidth. Weak Wi-Fi, large uploads on the same
connection, or VPN routing for a call that does not need it are the usual causes. If a
whole office is affected, the internet link is saturated.

## Resolution steps
1. Ask whether it happens on a cable too. If only on Wi-Fi, treat it as a Wi-Fi signal
   problem (move closer to an access point, or use a cable).
2. Check for large uploads or backups running at the same time.
3. If the user is on VPN for a call with outside participants, they can disconnect the VPN
   for the call.
4. Ask the user to run the call app's network test during a bad call and send the result.
5. If many users at one office are affected, escalate as a link-capacity problem.

## Warnings
Do not ask users to stop company backups to free bandwidth.

## Key facts
- Problems only on Wi-Fi point to a wireless signal issue.
- Disconnecting the VPN is acceptable for calls that need no internal access.
- Many users at one office with bad calls points to link capacity.
