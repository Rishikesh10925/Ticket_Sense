# Site-to-Site VPN Tunnel Down

**Department:** Networking

## Issue
Users at a branch office report they cannot reach resources at another
office or the main data center, while internet access from that branch
works normally.

## Resolution
1. Check the site-to-site VPN tunnel status on the local gateway/firewall —
   confirm whether it shows down, flapping, or up-but-not-passing-traffic.
2. A tunnel that's "up" but not passing traffic often indicates a routing
   table issue rather than the tunnel itself — check that routes to the
   remote subnet are present and correct.
3. Check both ends — an ISP change or IP change at either site can break
   the tunnel's pre-shared key/peer configuration.
4. This is a site-wide issue affecting all users at that branch; treat as
   high priority and escalate to network engineering rather than
   troubleshooting per-user.

## Notes
Confirm with the branch whether any local network changes (new firewall,
ISP switch) happened recently — this is the most common cause of a
previously-stable tunnel going down.
