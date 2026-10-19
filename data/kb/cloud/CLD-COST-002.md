---
id: CLD-COST-002
department: Cloud
topic: cloud-cost
title: Costs missing from the team's cost report
updated: '2025-12-15'
served: false
author: R
reviewer: null
---

## Symptom
A team's cost report shows less than expected, or a large amount appears as "untagged"
or "no cost centre".

## Cause
Costs are assigned to teams by tags. Resources created without the cost-centre tag are
not attributed, and a newly created tag key does not appear in cost reports until it is
activated as a cost allocation tag. Tags are never applied to past costs.

## Resolution steps
1. List the team's resources without the cost-centre tag and ask the owners to add it.
2. If a new tag key was introduced, ask the billing administrator to activate it as a
   cost allocation tag.
3. Explain that tagging and activation apply from that point on; earlier costs stay
   untagged in the reports.
4. Recommend enforcing the tag at creation with the landing-zone policy.

## Warnings
Do not edit past billing data by hand to move costs between teams.

## Key facts
- Costs are attributed to teams through the cost-centre tag.
- A new tag key must be activated as a cost allocation tag before it appears in cost reports.
- Tags and activation do not apply retroactively to past costs.
