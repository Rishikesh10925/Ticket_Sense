---
id: DB-CONN-001
department: Database
topic: db-connectivity
title: Application runs out of database connections
updated: '2026-07-02'
served: true
author: A
reviewer: null
legacy: connection-pool-exhausted
---

## Symptom
Application logs show "connection pool exhausted", "sorry, too many clients already", or
requests waiting for a database connection, while the database server is up.

## Cause
Either the database reached `max_connections`, or the application's pool is full because
code paths take connections and never return them (a leak), often after an unhandled
error. Sessions left "idle in transaction" also hold connection slots.

## Resolution steps
1. Compare the number of connections in `pg_stat_activity` with `SHOW max_connections`.
2. Group the sessions by application and state; many "idle in transaction" sessions from
   one application point to that application.
3. Check whether the errors started after a deployment; a new code path that does not
   close its connection is the usual cause.
4. As a stop-gap, restart the affected application instance to release leaked connections.
5. Send the findings to the owning team to fix the leak or pool settings.

## Warnings
Raising `max_connections` hides a leak and costs memory on the server; fix the leak first.

## Key facts
- "too many clients already" means the server reached max_connections.
- Sessions idle in transaction hold connection slots while doing no work.
- Restarting the application releases leaked connections but is only a stop-gap.
