---
id: NET-SW-003
department: Networking
topic: net-switching
title: Desk phone does not power on
updated: '2025-11-25'
served: false
author: R
reviewer: null
---

## Symptom
An IP desk phone stays dark when plugged into the wall port, while a laptop on the same
port gets a connection.

## Cause
IP phones are powered over the network cable (PoE). The switch port has PoE disabled, the
switch's PoE budget is used up, or the phone is plugged into a port on a non-PoE switch.

## Resolution steps
1. Check the phone is connected to the wall port, and the laptop (if any) to the phone's
   PC port.
2. Try the phone at a desk where a phone works. If it powers up there, the original port
   lacks power.
3. Ask network engineering to check PoE on that switch port and the switch's power budget.
4. If the phone does not power up anywhere, replace the phone.

## Warnings
Do not use a power injector from home; only approved ones may be used.

## Key facts
- IP desk phones are powered through the network cable (PoE).
- A phone that works at another desk shows the original port lacks PoE.
- Network engineering checks PoE settings and the switch power budget.
