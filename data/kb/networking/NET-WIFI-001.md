---
id: NET-WIFI-001
department: Networking
topic: net-wifi
title: Office Wi-Fi keeps dropping
updated: '2026-03-30'
served: true
author: R
reviewer: null
legacy: wifi-dropping-office
---

## Symptom
A laptop repeatedly disconnects from the office Wi-Fi, especially after being idle or
when the user moves between meeting rooms.

## Cause
Most often the adapter's power saving turns the radio down when idle, or the laptop holds
on to a distant access point. When many users in one area drop at once, an access point
or the wireless controller is at fault.

## Resolution steps
1. Ask whether colleagues in the same area are affected. If yes, record the location and
   escalate it as an access point problem.
2. Note the network name and the access point the laptop was last connected to, from the
   connection details.
3. Forget the network and reconnect to clear a stale saved profile.
4. Set the adapter's power management so Windows cannot turn it off to save power, and
   update the wireless driver from the software centre.

## Warnings
Do not tell users to connect to the guest network instead; it has no access to internal
systems.

## Key facts
- Drops after idle periods are usually caused by the adapter's power saving.
- Many users dropping in one area points to an access point or controller problem.
- Forgetting and re-adding the network clears a stale saved profile.
