---
id: NET-SW-004
department: Networking
topic: net-switching
title: Wired connection gives the wrong network after a move
updated: '2026-02-09'
served: false
author: R
reviewer: null
---

## Symptom
After a desk move, the user's wired connection works but they cannot reach their
department's systems or printers, or they get an address from another department's range.

## Cause
Each department's ports are placed in that department's VLAN. The new desk's port is
still in the previous occupant's VLAN.

## Resolution steps
1. Note the desk's wall port number and the user's department.
2. Run `ipconfig` and record the address range the laptop received.
3. Ask network engineering to move the switch port to the department's VLAN, giving the
   port number and department.
4. After the change, run `ipconfig /release` and `ipconfig /renew` and retest.

## Warnings
Do not swap patch cables at the panel to "borrow" another desk's port.

## Key facts
- Each department's desk ports belong to that department's VLAN.
- After a desk move the port may still be in the previous occupant's VLAN.
- VLAN changes are made by network engineering; the user then renews the DHCP lease.
