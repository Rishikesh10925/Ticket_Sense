---
id: NET-SW-002
department: Networking
topic: net-switching
title: Switch port in err-disabled state
updated: '2026-06-02'
served: false
author: R
reviewer: null
legacy: switch-port-error-disabled
---

## Symptom
A wired connection that worked stops working, and network engineering sees the switch
port in "err-disabled" state.

## Cause
The switch shut the port to protect the network: usually a loop (a small switch or a cable
connecting two wall ports) or a port-security violation (an unknown device's MAC address).

## Resolution steps
1. Check the switch log for the reason the port was disabled.
2. For a loop, find and remove the offending cable or desk switch before re-enabling.
3. For port security, confirm the new device is legitimate, then clear the violation.
4. Re-enable the port (shutdown and no shutdown on the interface) only after the cause is
   fixed.

## Warnings
Re-enabling an err-disabled port without fixing the cause makes it shut again within
minutes and can disrupt others on the same switch.

## Key facts
- Err-disabled ports are shut by the switch because of a loop or a port-security violation.
- The switch log states why the port was disabled.
- A port is re-enabled only after the cause is removed.
