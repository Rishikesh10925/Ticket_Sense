---
id: CLD-ENV-004
department: Cloud
topic: cloud-provisioning
title: Decommission a cloud environment
updated: '2024-11-12'
served: false
author: A
reviewer: null
---

## Symptom
A team says an application or project has ended and asks for its cloud resources or
environment to be removed.

## Cause
Decommissioning removes cost and attack surface, but data may need to be kept for
retention reasons first.

## Resolution steps
1. Confirm with the owner and the cost-centre manager that the environment is no longer
   used.
2. Check the data retention requirements for databases and storage.
3. Take final snapshots of databases and volumes where retention requires them, and record
   their IDs.
4. Delete the resources, then close the account or project through the platform team.

## Warnings
Never delete a database without a final snapshot unless the data owner confirms in writing
that none is needed.

## Key facts
- Decommissioning needs confirmation from the owner and the cost-centre manager.
- Final snapshots are taken where data retention requires them.
- Accounts and projects are closed by the platform team.
