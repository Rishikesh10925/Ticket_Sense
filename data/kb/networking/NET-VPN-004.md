---
id: NET-VPN-004
department: Networking
topic: net-vpn
title: VPN multi-factor prompt never arrives
updated: '2025-12-01'
served: true
author: R
reviewer: null
---

## Symptom
The VPN client accepts the user's password and then waits for a multi-factor approval
that never appears on their phone, until the connection times out.

## Cause
The authenticator app is not receiving push notifications: notifications are disabled,
the phone has no data connection, or the user has a new phone and the app was not moved
to it.

## Resolution steps
1. Ask whether the user recently changed or reset their phone.
2. Ask them to open the authenticator app directly; pending requests often show inside
   the app even when the notification did not.
3. If push still fails, the user can choose the one-time code option in the VPN client
   and type the code shown in the app.
4. If the app is on an old phone or was removed, verify the user's identity and
   re-register their authenticator through the identity team's process.

## Warnings
Never approve or disable multi-factor authentication on the user's behalf, and never
accept a code read out by someone whose identity has not been verified.

## Key facts
- Pending multi-factor requests can be approved by opening the authenticator app directly.
- The one-time code option works when push notifications fail.
- A new phone needs the authenticator re-registered after identity verification.
