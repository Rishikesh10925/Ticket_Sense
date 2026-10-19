---
id: CLD-COST-001
department: Cloud
topic: cloud-cost
title: Cloud cost anomaly alert
updated: '2026-03-03'
served: false
author: R
reviewer: null
legacy: cost-spike-alert
---

## Symptom
A cost anomaly alert fires for an unexpected increase in spending in a cloud account or
project.

## Cause
Usually a resource left running after a test, an auto-scaling group that scaled out and
did not scale back, or a jump in outbound data transfer. Some spikes are planned work.

## Resolution steps
1. Break the cost down by service for the alert period; this normally points to one
   service.
2. Find the resources behind the increase and their owner from the tags.
3. If the spend is planned (load test, migration), record that in the ticket and close.
4. If a resource is unintended, confirm with its owner, then stop or delete it.

## Warnings
Never delete a resource before confirming ownership: a "forgotten test" may be a
production dependency with a misleading name.

## Key facts
- A cost breakdown by service usually points to the cause at once.
- Owners are identified from resource tags.
- Resources are stopped only after the owner confirms they are unintended.
