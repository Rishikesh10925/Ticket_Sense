---
id: NET-PERF-003
department: Networking
topic: net-performance
title: File copies are very slow over VPN
updated: '2025-10-20'
served: true
author: R
reviewer: null
---

## Symptom
Opening or copying large files from a file share takes minutes over VPN, while it is fast
in the office.

## Cause
File shares are designed for low-latency office networks. Over the VPN each file
operation makes many round trips, so latency, not bandwidth, limits speed. Home Wi-Fi
adds more latency.

## Resolution steps
1. Check the user's home connection with a speed test, and ask them to use a cable or sit
   closer to the router.
2. For documents, recommend the company's synchronised cloud storage, which is designed
   for remote work.
3. For large files used often, copy them once and work locally, then copy back.
4. If speed is poor for all remote users at once, escalate as a VPN gateway capacity issue.

## Warnings
Do not tell users to email large files to themselves.

## Key facts
- File shares over VPN are limited by latency, not bandwidth.
- Synchronised cloud storage is the recommended option for remote document work.
- Slow speed for all remote users at once points to VPN gateway capacity.
