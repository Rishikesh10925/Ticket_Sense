# Fact-check checklist: NETWORKING (24 articles, reviewer A)

For each article: open it, click each term, confirm the article uses it correctly.
All correct ➜ set `reviewer: A` in the article. Something wrong ➜ note it here and tell Claude.
Values described as *this organisation's* policy (limits, approvals) are fictional company rules:
they cannot be looked up, only checked for being stated as policy rather than as a vendor default.
⭐ = check first (flagged as risky). ⬜ = not checked. 🤖 = AI-checked only (still needs a human). ✅ = human-reviewed.

## ⬜ NET-DNS-001: Internal names do not resolve
File: [data/kb/networking/NET-DNS-001.md](../../data/kb/networking/NET-DNS-001.md) · author R

**Look up:** [ipconfig /all](https://www.google.com/search?q=Windows+ipconfig+%2Fall+site%3Alearn.microsoft.com) · [ipconfig /flushdns](https://www.google.com/search?q=Windows+ipconfig+%2Fflushdns+site%3Alearn.microsoft.com)

**Key facts to confirm:**
- [ ] Working by IP but not by name isolates the problem to DNS.
- [ ] Internal names resolve only through the internal DNS servers.
- [ ] Public resolvers such as 8.8.8.8 cannot resolve internal names.

Notes: 

## ⬜ NET-DNS-002: Connected but no internet, 169.254 address
File: [data/kb/networking/NET-DNS-002.md](../../data/kb/networking/NET-DNS-002.md) · author R

**Look up:** [ipconfig](https://www.google.com/search?q=Windows+ipconfig+site%3Alearn.microsoft.com) · [ipconfig /release](https://www.google.com/search?q=Windows+ipconfig+%2Frelease+site%3Alearn.microsoft.com) · [ipconfig /renew](https://www.google.com/search?q=Windows+ipconfig+%2Frenew+site%3Alearn.microsoft.com) · [DHCP](https://www.google.com/search?q=Windows+DHCP+site%3Alearn.microsoft.com)

**Key facts to confirm:**
- [ ] A 169.254.x.x address means the device got no answer from DHCP.
- [ ] ipconfig /release then /renew requests a fresh lease.
- [ ] Many devices with 169.254 addresses point to the DHCP server or a full scope.

Notes: 

## ⬜ NET-DNS-003: Windows reports an IP address conflict
File: [data/kb/networking/NET-DNS-003.md](../../data/kb/networking/NET-DNS-003.md) · author R

**Look up:** [ipconfig /release](https://www.google.com/search?q=Windows+ipconfig+%2Frelease+site%3Alearn.microsoft.com) · [ipconfig /renew](https://www.google.com/search?q=Windows+ipconfig+%2Frenew+site%3Alearn.microsoft.com) · [DHCP](https://www.google.com/search?q=Windows+DHCP+site%3Alearn.microsoft.com)

**Key facts to confirm:**
- [ ] IP conflicts are usually caused by a static address inside the DHCP range.
- [ ] Renewing the DHCP lease gives the laptop a new address and restores the connection.
- [ ] The device with the static address must be reserved or moved outside the DHCP range.

Notes: 

## ⬜ NET-DNS-004: Server name points to the old address after a move
File: [data/kb/networking/NET-DNS-004.md](../../data/kb/networking/NET-DNS-004.md) · author R

**Look up:** [nslookup <name>](https://www.google.com/search?q=Windows+nslookup+%3Cname%3E+site%3Alearn.microsoft.com) · [ipconfig /flushdns](https://www.google.com/search?q=Windows+ipconfig+%2Fflushdns+site%3Alearn.microsoft.com) · [C:\Windows\System32\drivers\etc\hosts](https://www.google.com/search?q=Windows+C%3A%5CWindows%5CSystem32%5Cdrivers%5Cetc%5Chosts+site%3Alearn.microsoft.com)

**Key facts to confirm:**
- [ ] Clients cache DNS answers until the record's TTL expires.
- [ ] ipconfig /flushdns clears the local DNS cache.
- [ ] A hosts-file entry overrides DNS and can keep pointing to an old address.

Notes: 

## ⬜ NET-FW-001: Firewall rule needed for an application
File: [data/kb/networking/NET-FW-001.md](../../data/kb/networking/NET-FW-001.md) · author R

**Look up:** [Test-NetConnection <host> -Port <port>](https://www.google.com/search?q=Windows+Test-NetConnection+%3Chost%3E+-Port+%3Cport%3E+site%3Alearn.microsoft.com)

**Key facts to confirm:**
- [ ] A firewall request needs source, destination, port, protocol and business reason.
- [ ] Firewall changes go through the change process, never ad hoc.
- [ ] Temporary rules must carry an end date.
- [ ] Any-to-any rules are never allowed.

Notes: 

## ⬜ NET-FW-002: Work website blocked by the web proxy
File: [data/kb/networking/NET-FW-002.md](../../data/kb/networking/NET-FW-002.md) · author R

**Look up:** (no technical terms; check the steps make sense)

**Key facts to confirm:**
- [ ] The proxy blocks by content category, not usually by specific site.
- [ ] The block page shows the category that caused the block.
- [ ] Miscategorised sites are recategorised; others need an allow-list request.

Notes: 

## ⬜ NET-FW-003: Certificate errors in a desktop tool on the office network
File: [data/kb/networking/NET-FW-003.md](../../data/kb/networking/NET-FW-003.md) · author R

**Look up:** (no technical terms; check the steps make sense)

**Key facts to confirm:**
- [ ] The proxy re-signs inspected traffic with the company root certificate.
- [ ] Tools with their own certificate store must be pointed at the company root certificate.
- [ ] Disabling certificate verification is never an acceptable fix.

Notes: 

## ⬜ NET-FW-004: Application cannot send email from the office network
File: [data/kb/networking/NET-FW-004.md](../../data/kb/networking/NET-FW-004.md) · author R

**Look up:** [SMTP](https://www.google.com/search?q=Windows+SMTP+site%3Alearn.microsoft.com)

**Key facts to confirm:**
- [ ] Outbound port 25 is blocked except from the company mail relay.
- [ ] Devices and applications must send email through the internal mail relay.
- [ ] A new device needs its IP registered with the relay.

Notes: 

## ⬜ NET-PERF-001: Video calls freeze or lag
File: [data/kb/networking/NET-PERF-001.md](../../data/kb/networking/NET-PERF-001.md) · author R

**Look up:** [PERF](https://www.google.com/search?q=Windows+PERF+site%3Alearn.microsoft.com)

**Key facts to confirm:**
- [ ] Problems only on Wi-Fi point to a wireless signal issue.
- [ ] Disconnecting the VPN is acceptable for calls that need no internal access.
- [ ] Many users at one office with bad calls points to link capacity.

Notes: 

## ⬜ NET-PERF-002: Mapped network drive shows a red X
File: [data/kb/networking/NET-PERF-002.md](../../data/kb/networking/NET-PERF-002.md) · author R

**Look up:** [\\server\share](https://www.google.com/search?q=Windows+%5C%5Cserver%5Cshare+site%3Alearn.microsoft.com) · [PERF](https://www.google.com/search?q=Windows+PERF+site%3Alearn.microsoft.com)

**Key facts to confirm:**
- [ ] Testing the full path (\\server\share) separates a broken mapping from a server problem.
- [ ] A password change can leave outdated credentials in Credential Manager.
- [ ] Mapped drives work only on the corporate network or VPN.

Notes: 

## ⬜ NET-PERF-003: File copies are very slow over VPN
File: [data/kb/networking/NET-PERF-003.md](../../data/kb/networking/NET-PERF-003.md) · author R

**Look up:** [PERF](https://www.google.com/search?q=Windows+PERF+site%3Alearn.microsoft.com)

**Key facts to confirm:**
- [ ] File shares over VPN are limited by latency, not bandwidth.
- [ ] Synchronised cloud storage is the recommended option for remote document work.
- [ ] Slow speed for all remote users at once points to VPN gateway capacity.

Notes: 

## ⬜ NET-PERF-004: Internet slow for a whole floor
File: [data/kb/networking/NET-PERF-004.md](../../data/kb/networking/NET-PERF-004.md) · author R

**Look up:** [PERF](https://www.google.com/search?q=Windows+PERF+site%3Alearn.microsoft.com)

**Key facts to confirm:**
- [ ] Many users slow at once in one area points to a saturated shared link or uplink.
- [ ] Network engineering checks link utilisation and uplink errors.
- [ ] Related user reports are linked to one parent ticket.

Notes: 

## ⬜ NET-SW-001: Network port dead at a new desk
File: [data/kb/networking/NET-SW-001.md](../../data/kb/networking/NET-SW-001.md) · author R

**Look up:** [VLAN](https://www.google.com/search?q=Windows+VLAN+site%3Alearn.microsoft.com)

**Key facts to confirm:**
- [ ] Testing the cable at a working desk rules out the cable first.
- [ ] Patch panel labels drift after desk moves and must be checked physically.
- [ ] A port in the wrong VLAN needs a switch change by network engineering.

Notes: 

## ⬜ NET-SW-002: Switch port in err-disabled state
File: [data/kb/networking/NET-SW-002.md](../../data/kb/networking/NET-SW-002.md) · author R

**Look up:** (no technical terms; check the steps make sense)

**Key facts to confirm:**
- [ ] Err-disabled ports are shut by the switch because of a loop or a port-security violation.
- [ ] The switch log states why the port was disabled.
- [ ] A port is re-enabled only after the cause is removed.

Notes: 

## ⬜ NET-SW-003: Desk phone does not power on
File: [data/kb/networking/NET-SW-003.md](../../data/kb/networking/NET-SW-003.md) · author R

**Look up:** (no technical terms; check the steps make sense)

**Key facts to confirm:**
- [ ] IP desk phones are powered through the network cable (PoE).
- [ ] A phone that works at another desk shows the original port lacks PoE.
- [ ] Network engineering checks PoE settings and the switch power budget.

Notes: 

## ⬜ NET-SW-004: Wired connection gives the wrong network after a move
File: [data/kb/networking/NET-SW-004.md](../../data/kb/networking/NET-SW-004.md) · author R

**Look up:** [ipconfig](https://www.google.com/search?q=Windows+ipconfig+site%3Alearn.microsoft.com) · [ipconfig /release](https://www.google.com/search?q=Windows+ipconfig+%2Frelease+site%3Alearn.microsoft.com) · [ipconfig /renew](https://www.google.com/search?q=Windows+ipconfig+%2Frenew+site%3Alearn.microsoft.com) · [VLAN](https://www.google.com/search?q=Windows+VLAN+site%3Alearn.microsoft.com) · [DHCP](https://www.google.com/search?q=Windows+DHCP+site%3Alearn.microsoft.com)

**Key facts to confirm:**
- [ ] Each department's desk ports belong to that department's VLAN.
- [ ] After a desk move the port may still be in the previous occupant's VLAN.
- [ ] VLAN changes are made by network engineering; the user then renews the DHCP lease.

Notes: 

## ⬜ NET-VPN-001: VPN client not connecting
File: [data/kb/networking/NET-VPN-001.md](../../data/kb/networking/NET-VPN-001.md) · author R

**Look up:** (no technical terms; check the steps make sense)

**Key facts to confirm:**
- [ ] A hang at "Connecting" with no login prompt points to a network that blocks the VPN.
- [ ] A mobile hotspot test separates a blocking network from a client fault.
- [ ] Authentication errors are checked against a locked or expired domain account first.
- [ ] Many users failing at once means a gateway problem for network engineering.

Notes: 

## ⬜ NET-VPN-002: Branch office cannot reach the head office
File: [data/kb/networking/NET-VPN-002.md](../../data/kb/networking/NET-VPN-002.md) · author R

**Look up:** (no technical terms; check the steps make sense)

**Key facts to confirm:**
- [ ] A whole branch losing head-office systems while internet works points to the site-to-site tunnel.
- [ ] A tunnel that is up but passes no traffic usually has a routing problem.
- [ ] A changed public IP or ISP at either site breaks the tunnel peer settings.
- [ ] Site-to-site tunnel changes are made by network engineering.

Notes: 

## ⬜ NET-VPN-003: VPN connected but internal sites do not open
File: [data/kb/networking/NET-VPN-003.md](../../data/kb/networking/NET-VPN-003.md) · author R

**Look up:** [ipconfig /all](https://www.google.com/search?q=Windows+ipconfig+%2Fall+site%3Alearn.microsoft.com)

**Key facts to confirm:**
- [ ] Reaching a resource by IP but not by name over VPN is a DNS problem.
- [ ] The VPN adapter should list the internal DNS servers in ipconfig /all.
- [ ] A home network using the same private range as an internal network stops that traffic entering the tunnel.

Notes: 

## ⬜ NET-VPN-004: VPN multi-factor prompt never arrives
File: [data/kb/networking/NET-VPN-004.md](../../data/kb/networking/NET-VPN-004.md) · author R

**Look up:** (no technical terms; check the steps make sense)

**Key facts to confirm:**
- [ ] Pending multi-factor requests can be approved by opening the authenticator app directly.
- [ ] The one-time code option works when push notifications fail.
- [ ] A new phone needs the authenticator re-registered after identity verification.

Notes: 

## ⬜ NET-WIFI-001: Office Wi-Fi keeps dropping
File: [data/kb/networking/NET-WIFI-001.md](../../data/kb/networking/NET-WIFI-001.md) · author R

**Look up:** [WIFI](https://www.google.com/search?q=Windows+WIFI+site%3Alearn.microsoft.com)

**Key facts to confirm:**
- [ ] Drops after idle periods are usually caused by the adapter's power saving.
- [ ] Many users dropping in one area points to an access point or controller problem.
- [ ] Forgetting and re-adding the network clears a stale saved profile.

Notes: 

## ⬜ NET-WIFI-002: Wi-Fi access for a visitor
File: [data/kb/networking/NET-WIFI-002.md](../../data/kb/networking/NET-WIFI-002.md) · author R

**Look up:** [WIFI](https://www.google.com/search?q=Windows+WIFI+site%3Alearn.microsoft.com)

**Key facts to confirm:**
- [ ] Guest access must be sponsored by an employee.
- [ ] Guest credentials always expire, matching the visit.
- [ ] The guest network is isolated from internal systems by design.

Notes: 

## ⬜ NET-WIFI-003: Corporate Wi-Fi rejects login after a password change
File: [data/kb/networking/NET-WIFI-003.md](../../data/kb/networking/NET-WIFI-003.md) · author R

**Look up:** [WIFI](https://www.google.com/search?q=Windows+WIFI+site%3Alearn.microsoft.com)

**Key facts to confirm:**
- [ ] Corporate Wi-Fi uses the domain account, so a password change breaks saved Wi-Fi credentials.
- [ ] Devices with the old saved password can lock the domain account.
- [ ] Forgetting the network on every device and reconnecting with the new password fixes it.

Notes: 

## ⬜ NET-WIFI-004: Laptop cannot see the corporate Wi-Fi network
File: [data/kb/networking/NET-WIFI-004.md](../../data/kb/networking/NET-WIFI-004.md) · author R

**Look up:** [WIFI](https://www.google.com/search?q=Windows+WIFI+site%3Alearn.microsoft.com)

**Key facts to confirm:**
- [ ] The corporate Wi-Fi network is broadcast only on 5 GHz.
- [ ] An adapter limited to 2.4 GHz or an old driver hides the corporate network.
- [ ] Airplane mode or a hardware Wi-Fi switch hides all networks.

Notes: 

