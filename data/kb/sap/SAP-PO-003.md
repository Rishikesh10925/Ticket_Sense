---
id: SAP-PO-003
department: SAP
topic: sap-procurement
title: Goods receipt quantity exceeds the PO quantity
updated: '2025-07-29'
served: true
author: S
reviewer: null
---

## Symptom
MIGO refuses the goods receipt because the quantity entered is larger than the open
quantity on the purchase order, even though the vendor really delivered that amount.

## Cause
Each PO item has an over-delivery tolerance (a percentage on the item's Delivery tab).
Receipts above the ordered quantity plus that tolerance are blocked, unless the item
allows unlimited over-delivery.

## Resolution steps
1. Display the PO in ME23N and note the ordered quantity, the quantity already received
   and the over-delivery tolerance on the item's Delivery tab.
2. Post a goods receipt for the quantity that is allowed (up to the tolerance) if the
   receiving team wants to accept that part now.
3. For the extra quantity, ask the buyer whether to accept it. If yes, the buyer
   increases the PO quantity in ME22N and the rest is received afterwards.
4. If the buyer does not accept the extra quantity, it is returned to the vendor.

## Warnings
Do not ask for the tolerance to be raised to "unlimited" to get one delivery through; it
removes the control for every future receipt on that item.

## Key facts
- The over-delivery tolerance is set per PO item on its Delivery tab.
- Receipts above ordered quantity plus tolerance are blocked in MIGO.
- The buyer decides whether to accept extra quantity by increasing the PO quantity.
