---
id: CLD-ENV-002
department: Cloud
topic: cloud-provisioning
title: Managed database refusing new connections
updated: '2026-05-05'
served: false
author: A
reviewer: null
legacy: database-connection-timeout
---

## Symptom
An application logs connection timeouts or "too many connections" errors against a
managed cloud database.

## Cause
The database reached its maximum number of connections. More often than a capacity
problem, the application opens connections without returning them to its pool (a
connection leak), especially after a deployment.

## Resolution steps
1. Compare the current connection count with the database's maximum connections setting.
2. Check whether the problem started after a deployment that changed connection pool
   settings.
3. Check database CPU and memory; heavy load makes queries and their connections pile up.
4. Ask the owning team to fix leaks or pool settings before resizing the database.

## Warnings
Raising the maximum connections or the instance size can hide a connection leak.

## Key facts
- "Too many connections" means the database reached its maximum connections setting.
- Connection leaks after a deployment are a common cause.
- Leaks are fixed before the database is resized.
