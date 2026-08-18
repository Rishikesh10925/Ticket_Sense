# Cannot Resolve Internal Hostnames

**Department:** Networking

## Issue
User can browse the internet fine but cannot reach internal resources by
name (e.g., `\\fileserver\share` or `intranet.company.local` fails, while
the same resource works by IP address).

## Resolution
1. Confirm the device is on the corporate network or VPN — internal DNS
   only resolves from those networks.
2. Run `ipconfig /all` and confirm the DNS servers listed match the internal
   DNS servers (public DNS like 8.8.8.8 won't resolve internal names).
3. If the wrong DNS servers are set, this is usually a DHCP or VPN config
   issue rather than something the user changed manually — check the VPN
   profile's DNS push settings.
4. Flush the local DNS cache (`ipconfig /flushdns`) and retry after
   confirming the correct DNS servers are in use.

## Notes
Resolving by IP but not by name almost always isolates the problem to DNS,
not general connectivity — don't spend time re-checking cabling/Wi-Fi once
this is confirmed.
