---
id: DB-HA-003
department: Database
topic: db-replication
title: Writes fail with read-only transaction error
updated: '2026-06-11'
served: false
author: A
reviewer: null
---

## Symptom
An application fails with "cannot execute INSERT in a read-only transaction" (or UPDATE
or DELETE).

## Cause
The application is connected to a read replica or a standby, which only accepts reads.
After a failover, an application may still point to the old primary, which has become a
standby.

## Resolution steps
1. Check which host the application is connected to.
2. Compare it with the current primary from the cluster status.
3. Correct the connection string, or use the cluster's write endpoint that always points
   to the primary.
4. Restart the application's connection pool so it reconnects.

## Warnings
Do not try to make the replica writable; it would break replication.

## Key facts
- "read-only transaction" errors mean the application is connected to a replica or standby.
- After a failover, the old primary can become a standby.
- Applications should use the cluster's write endpoint, which follows the primary.
