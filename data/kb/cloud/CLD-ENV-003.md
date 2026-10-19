---
id: CLD-ENV-003
department: Cloud
topic: cloud-provisioning
title: Request for a new managed database
updated: '2026-08-12'
served: false
author: A
reviewer: null
---

## Symptom
A team asks for a managed database (for example PostgreSQL or MySQL) for a new
application.

## Cause
Managed databases are provisioned by the platform team from approved configurations, with
backups, encryption and network placement set by policy.

## Resolution steps
1. Collect engine and version, environment, expected size, the owning team and the
   application that will connect.
2. Choose the approved configuration: production databases are deployed across two
   availability zones; development databases may use one.
3. Ensure automated backups and encryption at rest are enabled; they are mandatory.
4. Place the database in private subnets and allow access only from the application's
   security group.

## Warnings
Managed databases are never given a public endpoint.

## Key facts
- Production databases are deployed across two availability zones.
- Automated backups and encryption at rest are mandatory.
- Databases sit in private subnets, reachable only from the application's security group.
