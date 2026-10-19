---
id: NET-DNS-001
department: Networking
topic: net-addressing
title: Internal names do not resolve
updated: '2026-04-04'
served: true
author: R
reviewer: null
legacy: dns-internal-hostname-fail
---

## Symptom
Public websites work, but internal names such as the intranet or a file server do not
open. The same resource opens when the user types its IP address.

## Cause
The device is not using the internal DNS servers: it is off the corporate network or VPN,
or it has public DNS servers set, which cannot resolve internal names.

## Resolution steps
1. Confirm the device is on the corporate network or connected to the VPN.
2. Run `ipconfig /all` and check that the DNS servers are the internal ones, not public
   resolvers such as 8.8.8.8.
3. If public DNS servers were set by hand, set the adapter back to obtain DNS
   automatically.
4. Run `ipconfig /flushdns` and retry.

## Warnings
Once the IP address works but the name does not, do not keep checking cables and Wi-Fi;
it is a DNS problem.

## Key facts
- Working by IP but not by name isolates the problem to DNS.
- Internal names resolve only through the internal DNS servers.
- Public resolvers such as 8.8.8.8 cannot resolve internal names.
