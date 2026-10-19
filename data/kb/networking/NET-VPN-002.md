---
id: NET-VPN-002
department: Networking
topic: net-vpn
title: Branch office cannot reach the head office
updated: '2026-08-19'
served: true
author: R
reviewer: null
legacy: site-to-site-vpn-down
---

## Symptom
Everyone at a branch office can browse the internet but cannot reach systems at the head
office or data centre: file shares, SAP and intranet sites all time out.

## Cause
The site-to-site VPN tunnel between the branch firewall and head office is down, or it is
up but routes to the remote networks are missing. Common triggers are an ISP change or new
public IP at either site, or a firewall replacement at the branch.

## Resolution steps
1. Confirm the scope: if all users at the branch are affected, treat it as a site outage
   with high priority.
2. Check the tunnel status on the branch firewall: down, flapping, or up without traffic.
3. If the tunnel is up but nothing passes, check the routes to the head-office networks.
4. Ask the branch whether anything changed recently: ISP, public IP address or firewall.
   Either end changing its public IP breaks the tunnel's peer settings.
5. Escalate to network engineering with the findings; tunnel changes are made by them.

## Warnings
Do not tell users to connect with the personal VPN client from inside the office as a
workaround; it overloads the remote-access gateway.

## Key facts
- A whole branch losing head-office systems while internet works points to the site-to-site tunnel.
- A tunnel that is up but passes no traffic usually has a routing problem.
- A changed public IP or ISP at either site breaks the tunnel peer settings.
- Site-to-site tunnel changes are made by network engineering.
