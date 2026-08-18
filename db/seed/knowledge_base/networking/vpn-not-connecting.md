# VPN Client Not Connecting

**Department:** Networking

## Issue
VPN client fails to establish a connection, hangs at "Connecting...", or
fails immediately with an authentication or timeout error.

## Resolution
1. Confirm the user's internet connection works independently of VPN (load
   any public website).
2. Restart the VPN client application, then retry.
3. If authentication fails specifically, confirm the account isn't locked
   (see SAP KB "Locked User Account" for the analogous AD lockout pattern —
   ask the user to try their normal domain login on a company laptop first).
4. If the client hangs at "Connecting" with no auth prompt, the VPN gateway
   may be unreachable from the user's network (common on hotel/public Wi-Fi
   that blocks the VPN port) — have them try a mobile hotspot to isolate.
5. Restart the machine if the VPN adapter shows as disabled in network
   settings after a Windows update.

## Notes
If multiple users report VPN failures simultaneously, check gateway status
before troubleshooting individual clients — this is often a service-side
outage.
