---
id: CLD-COST-003
department: Cloud
topic: cloud-cost
title: Unexpected data transfer charges
updated: '2026-07-08'
served: false
author: R
reviewer: null
---

## Symptom
The bill shows high data transfer or network charges that the team cannot explain,
although compute and storage costs are normal.

## Cause
Data leaving the cloud to the internet is charged, and traffic between availability zones
or regions is charged too. Traffic from private subnets that goes out through a NAT
gateway also pays a per-gigabyte processing charge.

## Resolution steps
1. Break the data transfer cost down by usage type: internet egress, inter-zone,
   inter-region or NAT gateway processing.
2. For NAT gateway charges, check whether instances download large data from storage
   through the NAT gateway; a gateway endpoint for the storage service avoids that charge.
3. For inter-zone charges, check whether chatty services were placed in different zones.
4. Share the findings with the owning team for an architecture fix.

## Warnings
Do not remove NAT gateways or endpoints yourself; it breaks connectivity for the workloads.

## Key facts
- Data leaving the cloud to the internet is charged; inbound data is not.
- Traffic through a NAT gateway pays an extra per-gigabyte processing charge.
- Traffic between availability zones is also charged.
