---
id: SAP-MAT-003
department: SAP
topic: sap-materials
title: Material not maintained for the plant
updated: '2026-04-16'
served: true
author: S
reviewer: Claude
---

## Symptom
Creating a purchase order, goods movement or production order fails with a message that
the material is not maintained in that plant (or for that storage location).

## Cause
Material master data is organised in views. A material can exist for one plant without
having been extended to another. Each plant needs its own plant-level views before the
material can be used there.

## Resolution steps
1. Note the material number, the plant and, if mentioned, the storage location.
2. Check in MM03 which plants the material is maintained for.
3. Ask the master-data team to extend the material to the missing plant (and storage
   location if needed) with MM01. Include who requested it and why.
4. Retry the original transaction once the extension is confirmed.

## Warnings
Do not use a similar material that already exists in the plant as a workaround: stock
and costs would be posted to the wrong material.

## Key facts
- A material must be extended to each plant before it can be used there.
- MM03 shows which plants a material is maintained for.
- Extensions are made by the master-data team in MM01.
