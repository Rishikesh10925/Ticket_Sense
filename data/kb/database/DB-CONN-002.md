---
id: DB-CONN-002
department: Database
topic: db-connectivity
title: Application times out connecting to the database
updated: '2026-02-13'
served: true
author: A
reviewer: null
legacy: db-connection-timeout-app
---

## Symptom
An application intermittently times out connecting to the database, while connecting
with a database client from another machine works.

## Cause
The difference is in the application's environment: the network path from the
application host, a full connection pool, a connect timeout set too short, or a
scheduled job that saturates the database at certain times.

## Resolution steps
1. Check whether the database was at its connection limit when the timeouts happened.
2. Test the connection from the application host itself; a client working from elsewhere
   does not prove the application's network path.
3. Check the application's connect timeout setting; very short values fail under mild load.
4. If timeouts cluster at the same time of day, look for a backup or batch job then.

## Warnings
Do not open the database to wider networks to "test"; test from the application host.

## Key facts
- A client working from another host does not rule out the application host's network path.
- A connect timeout set too short causes intermittent failures under load.
- Timeouts at the same time each day point to a scheduled job.
