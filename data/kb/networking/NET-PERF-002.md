---
id: NET-PERF-002
department: Networking
topic: net-performance
title: Mapped network drive shows a red X
updated: '2026-03-11'
served: true
author: R
reviewer: null
legacy: mapped-drive-inaccessible
---

## Symptom
A mapped network drive shows as disconnected with a red X, or opening it gives "network
path not found".

## Cause
The device is off the corporate network, the saved credentials are outdated after a
password change, or the file server is down.

## Resolution steps
1. Confirm the device is on the corporate network or VPN.
2. Open the share by its full path (`\\server\share`). If that works, only the mapping is
   broken: remove and re-add the mapped drive.
3. If the user changed their password recently, update the saved credentials in Windows
   Credential Manager.
4. If the full path fails too, ask whether colleagues using the same server are affected.
   If so, escalate to the server team.

## Warnings
Do not copy files to personal cloud storage as a workaround for an unreachable share.

## Key facts
- Testing the full path (\\server\share) separates a broken mapping from a server problem.
- A password change can leave outdated credentials in Credential Manager.
- Mapped drives work only on the corporate network or VPN.
