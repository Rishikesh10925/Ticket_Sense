---
id: DB-PERF-003
department: Database
topic: db-performance
title: Database server CPU is very high
updated: '2026-09-17'
served: true
author: A
reviewer: null
---

## Symptom
Monitoring shows the database server's CPU near 100 percent and applications are slow.

## Cause
A few expensive queries usually cause most of the load: a new query without a suitable
index, a report run at peak time, or a query whose plan changed after data growth.

## Resolution steps
1. Look at `pg_stat_activity` for long-running active queries right now.
2. Check `pg_stat_statements` for the queries with the highest total execution time.
3. If one report or job causes the spike, ask its owner to stop it or run it off-peak.
4. Send the top queries and their plans to the owning teams for tuning.

## Warnings
Do not restart the database to clear CPU load; it drops every connection and the load
usually returns.

## Key facts
- pg_stat_statements ranks queries by total execution time.
- High CPU is usually caused by a few expensive queries.
- Restarting the database is not a fix for high CPU.
