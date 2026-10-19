---
id: SAP-MAT-002
department: SAP
topic: sap-materials
title: Number range exhausted
updated: '2024-12-10'
served: true
author: S
reviewer: null
legacy: number-range-exhausted
---

## Symptom
Creating a document (material, purchase order, sales order or accounting document) fails
because no number can be assigned: the message says the number range interval is full or
was not found.

## Cause
Every document type draws its numbers from a number range interval. When the interval
reaches its upper limit, or the interval for a new fiscal year was never created, no new
documents of that type can be saved.

## Resolution steps
1. Note the exact message, the document type and the company code or plant.
2. Identify the number range object (for example FBN1 for accounting documents, MMNR for
   materials, or SNRO for the generic view).
3. Escalate to the SAP configuration team with the object, the interval and the fiscal
   year. Extending or adding an interval is a configuration change.
4. If the error appeared at the start of a fiscal year, mention it: the new year's
   interval may simply not have been created.

## Warnings
The helpdesk never changes number ranges. Changing the current number of an interval by
hand can create duplicate document numbers.

## Key facts
- Each document type draws numbers from a number range interval.
- Year-dependent intervals, such as accounting documents, must be created for every new fiscal year.
- Number range changes are configuration changes made by the SAP configuration team.
