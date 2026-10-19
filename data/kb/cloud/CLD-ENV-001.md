---
id: CLD-ENV-001
department: Cloud
topic: cloud-provisioning
title: Request for a new cloud environment
updated: '2025-07-01'
served: false
author: A
reviewer: null
legacy: new-environment-provisioning
---

## Symptom
A team asks for a new cloud account or project for a new application, or for development,
test or production.

## Cause
New environments must come from the standard landing-zone template, which sets up security
guardrails, logging and cost tags.

## Resolution steps
1. Collect the purpose, owning team, environment type (development, test, staging or
   production) and expected size.
2. Provision the environment from the landing-zone template; never create it by hand.
3. Apply the required tags (cost centre, owner, environment) at creation.
4. Give the team least-privilege access; broader access is a separate request.

## Warnings
"Clone the existing environment" requests also go through the template; clones carry over
overly broad permissions.

## Key facts
- New environments are created only from the landing-zone template.
- Cost-centre, owner and environment tags are applied at creation.
- Teams get least-privilege access by default.
