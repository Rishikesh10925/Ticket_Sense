# ME023: Purchase Order Item Blocked

**Department:** SAP

## Issue
Posting a goods receipt against a purchase order fails with error **ME023
"Item is blocked" / "Purchase order item X is blocked for posting"**. This
appears in MIGO when the PO line has a delivery or invoice block.

## Resolution
1. Open the PO in ME23N and check the **Delivery** and **Invoice** tabs for a
   block reason (price variance, quantity variance, or manual block).
2. If the block was set manually by a buyer, ask the requesting department to
   release it via ME29N before retrying MIGO.
3. If it's a system-set variance block, verify the PO price/quantity matches
   the vendor's delivery note. Correct the PO line if the vendor data was
   entered wrong.
4. Retry the goods receipt once the block is cleared.

## Notes
Blocks tied to a price variance greater than the configured tolerance require
buyer sign-off — the helpdesk cannot release these directly.
