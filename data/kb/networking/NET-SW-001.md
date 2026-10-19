---
id: NET-SW-001
department: Networking
topic: net-switching
title: Network port dead at a new desk
updated: '2025-03-04'
served: false
author: R
reviewer: null
legacy: new-desk-vlan-port
---

## Symptom
A wired port at a new or reassigned desk shows no link light or "network cable unplugged",
even though a cable is connected.

## Cause
The wall port is not patched to the switch, is patched to the wrong switch port, or the
switch port is not set to the right VLAN for that area. Ports in newly built areas may not
be activated yet.

## Resolution steps
1. Test the cable at a desk where the network works, to rule out the cable.
2. Check the desk's port number against the patch panel; desk moves leave stale labels.
3. If the patch is right, ask network engineering to check the switch port is enabled and
   in the correct VLAN.
4. For a newly built area, check the office fit-out ticket before treating it as a fault.

## Warnings
Do not plug the desk into a different wall port that belongs to another desk or a
printer.

## Key facts
- Testing the cable at a working desk rules out the cable first.
- Patch panel labels drift after desk moves and must be checked physically.
- A port in the wrong VLAN needs a switch change by network engineering.
