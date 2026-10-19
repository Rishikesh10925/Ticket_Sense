---
id: NET-DNS-004
department: Networking
topic: net-addressing
title: Server name points to the old address after a move
updated: '2026-09-29'
served: true
author: R
reviewer: null
---

## Symptom
After a server or application was moved, some users still reach the old system or get
timeouts, while others reach the new one without problems.

## Cause
Clients cache DNS answers for the record's time-to-live (TTL). Until the cached entry
expires, a client keeps using the old IP address. Local hosts-file entries cause the same
effect permanently.

## Resolution steps
1. Run `nslookup <name>` on the user's machine and compare the answer with the new address.
2. If the answer is old, run `ipconfig /flushdns` and test again.
3. Check the hosts file (`C:\Windows\System32\drivers\etc\hosts`) for an entry for that
   name and remove it.
4. If the DNS server itself still answers with the old address, escalate to the team that
   owns the DNS record.

## Warnings
Do not edit DNS records yourself; ask the record owner.

## Key facts
- Clients cache DNS answers until the record's TTL expires.
- ipconfig /flushdns clears the local DNS cache.
- A hosts-file entry overrides DNS and can keep pointing to an old address.
