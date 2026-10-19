# Video Calls Dropping or Lagging

**Department:** Networking

## Issue
Video/audio calls (Teams, Zoom, etc.) frequently freeze, drop, or have
noticeable lag, while general web browsing seems unaffected.

## Resolution
1. Check whether the issue happens on both Wi-Fi and wired connections — if
   only on Wi-Fi, it's likely a wireless signal/interference issue rather
   than a WAN bandwidth problem.
2. Confirm no large downloads/uploads (backups, big file transfers) are
   running concurrently on the same network segment.
3. Have the user run a speed/latency test during a call to capture actual
   conditions, rather than relying on a later retest.
4. If the issue is consistent for all users on a specific office/link (not
   just one person), escalate as a possible WAN capacity issue rather than
   continuing single-user troubleshooting.

## Notes
VPN adds latency by design — if the user is on VPN for a call that doesn't
require internal network access, having them disconnect VPN for that call is
a valid workaround.
