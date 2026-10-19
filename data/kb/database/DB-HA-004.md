---
id: DB-HA-004
department: Database
topic: db-replication
title: Inactive replication slot
updated: '2024-09-17'
served: false
author: A
reviewer: null
---

## Symptom
Monitoring reports an inactive replication slot, often together with growing disk use on
the primary.

## Cause
A replication slot makes the primary keep WAL until the consumer (a replica or a logical
replication subscriber) has received it. If that consumer is gone or stopped, WAL builds
up without limit.

## Resolution steps
1. List slots with `pg_replication_slots` and find those with `active = false`.
2. Identify the consumer: a decommissioned replica, or a stopped subscriber.
3. If the consumer is needed, restart or repair it so the slot becomes active again.
4. If it is gone for good, the DBA team drops the slot with
   `pg_drop_replication_slot`; the replica will need a rebuild if it returns later.

## Warnings
Dropping a slot that a live replica still needs forces that replica to be rebuilt.

## Key facts
- An inactive replication slot makes the primary keep WAL indefinitely.
- pg_replication_slots shows which slots are inactive.
- Dropping a slot used by a live replica forces a rebuild of that replica.
