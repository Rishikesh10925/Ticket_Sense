---
id: CLD-VM-002
department: Cloud
topic: cloud-compute
title: Restore a disk or server from a snapshot
updated: '2026-04-21'
served: true
author: A
reviewer: null
legacy: snapshot-restore-request
---

## Symptom
A team asks to restore a disk, database or virtual machine from a snapshot after an
accidental deletion, corruption or a bad change.

## Cause
Snapshots capture a resource at a point in time. Restoring creates a resource from that
point; anything changed after the snapshot is not in it.

## Resolution steps
1. Confirm the exact resource, the point in time needed, and why.
2. Restore to a new resource rather than overwriting the original, so the current state
   is not lost if the wrong snapshot was chosen.
3. With the owner, check the restored copy contains the expected data.
4. Update anything that points to the old resource (DNS names, connection strings) only
   after the copy is verified.
5. Record the snapshot ID and time in the ticket.

## Warnings
Never delete the original resource before the restored copy is verified.

## Key facts
- Restores go to a new resource by default, not over the original.
- Data changed after the snapshot time is not in the restored copy.
- The original is kept until the restored copy is verified by the owner.
