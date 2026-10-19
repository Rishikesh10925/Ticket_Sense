---
id: CLD-VM-004
department: Cloud
topic: cloud-compute
title: Development server stopped overnight
updated: '2025-08-26'
served: true
author: A
reviewer: null
---

## Symptom
A developer finds their development or test virtual machine stopped every morning or at
weekends, and asks who keeps turning it off.

## Cause
Development and test machines are stopped outside working hours by the instance scheduler,
based on a schedule tag, to save cost. Production machines are excluded.

## Resolution steps
1. Check the machine's schedule tag; it shows which schedule applies.
2. Explain the schedule and that the developer can start the machine when needed.
3. If the work genuinely needs the machine to run overnight (for example a long test),
   the owner can change the tag to another approved schedule for a set period.
4. Note that local data on instance-store disks is lost when the machine stops; data must
   live on persistent volumes.

## Warnings
Do not remove the schedule tag permanently from development machines.

## Key facts
- Development and test machines are stopped outside working hours by the instance scheduler.
- The machine's schedule tag decides when it is stopped.
- Data on instance-store disks is lost when the machine stops.
