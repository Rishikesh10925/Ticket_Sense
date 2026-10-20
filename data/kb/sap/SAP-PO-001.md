---
id: SAP-PO-001
department: SAP
topic: sap-procurement
title: Goods receipt fails because the PO item is blocked
updated: '2026-09-02'
served: true
author: S
reviewer: Claude
legacy: me023-error-goods-receipt
---

## Symptom
Posting a goods receipt in MIGO against a purchase order fails with a message that the
purchase order item is blocked, so the goods cannot be received.

## Cause
A buyer has blocked the PO item in ME22N (for example during a dispute with the
vendor), or the item has a deletion indicator. Blocked items cannot be received until a
buyer releases them.

## Resolution steps
1. Display the PO in ME23N and open the item. Check whether the item shows a block or a
   deletion indicator in the item overview.
2. Find the buyer from the PO header (purchasing group) and ask whether the block is
   intentional.
3. If the block should be removed, the buyer removes it in ME22N and saves the PO.
4. Retry the goods receipt in MIGO.
5. If the item has a deletion indicator and the goods have physically arrived, the buyer
   must create a new PO item; a deleted item cannot be received.

## Warnings
The helpdesk does not change purchase orders. Only the responsible buyer removes a block.

## Key facts
- A blocked PO item cannot be goods-receipted in MIGO until the buyer removes the block.
- Blocks are removed by the responsible buyer in ME22N, never by the helpdesk.
- ME23N displays the PO without changing it.
- An item with a deletion indicator needs a new PO item instead of a receipt.
