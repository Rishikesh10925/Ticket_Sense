---
id: CLD-VM-003
department: Cloud
topic: cloud-compute
title: Virtual machine disk is full
updated: '2026-01-06'
served: true
author: A
reviewer: null
---

## Symptom
An application on a cloud virtual machine fails to write files or logs, services stop, or
SSH sessions fail, and the disk shows 100 percent used.

## Cause
Logs or data filled the volume. Growing the cloud volume alone is not enough: the
partition and file system inside the machine must also be extended.

## Resolution steps
1. If you can still log in, find what is using the space (for example old logs) and ask
   the owner whether it can be removed.
2. To add space, increase the volume size in the cloud console.
3. Inside the machine, extend the partition (`growpart`) and then the file system
   (`resize2fs` for ext4 or `xfs_growfs` for XFS).
4. Ask the owner to set up log rotation so it does not fill again.

## Warnings
Take a snapshot of the volume before resizing.

## Key facts
- Growing a cloud volume does not grow the file system automatically.
- The partition is extended with growpart and the file system with resize2fs or xfs_growfs.
- A snapshot is taken before resizing a volume.
