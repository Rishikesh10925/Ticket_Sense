# Switch Port Error-Disabled

**Department:** Networking

## Issue
A previously working wired connection stops working, and the switch shows
the port in "err-disabled" status.

## Resolution
1. Check the switch logs for the reason the port was disabled — common
   causes are a spanning-tree loop (someone plugged a switch into a switch)
   or port security violation (unrecognized MAC address).
2. If caused by a loop, identify and remove the offending cable/device
   before re-enabling the port — re-enabling without fixing the cause will
   just trigger the same shutdown again.
3. If caused by port security (e.g., a new device replaced an old one at
   that desk), verify the new device is legitimate, then clear the port
   security violation and re-enable.
4. Re-enable via `shutdown` / `no shutdown` on the interface, or the
   equivalent in the switch's management UI.

## Notes
Never just re-enable an err-disabled port without checking the reason first
— it will usually just disable again within minutes if the root cause isn't
addressed.
