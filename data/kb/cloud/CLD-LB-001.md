---
id: CLD-LB-001
department: Cloud
topic: cloud-traffic
title: Load balancer marks servers unhealthy
updated: '2026-06-17'
served: true
author: A
reviewer: null
legacy: load-balancer-health-check-failing
---

## Symptom
The load balancer marks one or more backend servers unhealthy, so capacity drops or
requests fail intermittently.

## Cause
The health check request fails: the application does not answer the configured path with
the expected status code, it answers too slowly, or a security group blocks the load
balancer from reaching the server.

## Resolution steps
1. Check the health check path, port and expected status code in the target settings.
2. Call that path directly on an affected server and check the response code and time.
3. If the server answers correctly but is still unhealthy, check the security group allows
   traffic from the load balancer, and the timeout and threshold settings.
4. If the application fails the check (slow start, a dependency down), route it to the
   owning team.

## Warnings
Do not point the health check at a page that always returns 200 regardless of
application state; it hides real failures.

## Key facts
- Health checks fail when the path does not return the expected status code in time.
- Calling the health check path directly on the server isolates application from network problems.
- Servers flapping between healthy and unhealthy usually lack CPU or memory.
