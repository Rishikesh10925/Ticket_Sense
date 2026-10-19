---
id: DB-HA-002
department: Database
topic: db-replication
title: Automatic failover did not happen
updated: '2025-10-28'
served: false
author: A
reviewer: null
legacy: failover-not-triggering
---

## Symptom
The primary database failed but the standby was not promoted automatically, or promotion
took much longer than expected.

## Cause
The failover health check still saw the primary as up (for example it only checked the
port), the failover system waited through what looked like a short blip, or there was no
quorum to decide safely.

## Resolution steps
1. Restore service first: if failover clearly should have happened, the DBA team promotes
   the standby manually.
2. Point applications at the new primary if they do not follow automatically.
3. Then review the health check, the failover delay and the quorum setup.
4. Schedule a failover drill once the system is stable.

## Warnings
Never promote a standby while the old primary may still accept writes; it causes split
brain.

## Key facts
- A health check that only tests the port can keep a broken primary looking healthy.
- Service is restored first by promoting the standby manually.
- Promoting while the old primary still accepts writes causes split brain.
