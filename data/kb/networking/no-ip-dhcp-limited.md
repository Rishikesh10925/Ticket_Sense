# Laptop Shows 'Limited Connectivity' (No IP Assigned)

**Department:** Networking

## Issue
Device connects to a network (Wi-Fi or wired) but shows "limited" or "no
internet" status, and `ipconfig` shows a 169.254.x.x address instead of a
normal internal IP.

## Resolution
1. A 169.254.x.x address means the device failed to get a response from
   DHCP and self-assigned a fallback address — this is a DHCP issue, not a
   general network outage.
2. Disconnect and reconnect to the network to trigger a new DHCP request.
3. Run `ipconfig /release` then `ipconfig /renew` (may require admin rights)
   to force a fresh lease.
4. If this recurs on the same port/AP for multiple devices, the DHCP scope
   may be exhausted — escalate to check available lease pool size.

## Notes
A single device repeatedly failing DHCP while others on the same network
succeed usually points to a bad network cable or NIC driver, not the DHCP
server.
