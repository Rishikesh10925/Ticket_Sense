---
id: DB-HA-001
department: Database
topic: db-replication
title: Read replica lagging behind
updated: '2026-02-02'
served: false
author: A
reviewer: null
legacy: replication-lag-alert
---

## Symptom
Monitoring reports replication lag above the threshold, or users see old data on pages
served from the read replica.

## Cause
A burst of writes on the primary (bulk import, batch update), a replica too small to
replay the write volume, or a long-running query on the replica that delays replay.

## Resolution steps
1. Check the primary's write volume when the lag started; burst lag recovers on its own.
2. Check the replica's CPU and disk I/O for sustained overload.
3. Look for long-running queries on the replica that hold up replay.
4. If lag keeps growing without a burst, escalate before the replica needs a full rebuild.

## Warnings
Features that need to read their own writes must read from the primary, not the replica.

## Key facts
- Lag caused by a write burst usually recovers after the burst.
- Long-running queries on a replica can delay replay.
- Read-your-own-writes features must read from the primary.
