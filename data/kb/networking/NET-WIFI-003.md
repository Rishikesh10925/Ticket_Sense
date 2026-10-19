---
id: NET-WIFI-003
department: Networking
topic: net-wifi
title: Corporate Wi-Fi rejects login after a password change
updated: '2026-07-15'
served: true
author: R
reviewer: null
---

## Symptom
Right after changing their domain password, the user's laptop or phone cannot join the
corporate Wi-Fi: it keeps asking for credentials or says it cannot connect to the network.

## Cause
The corporate Wi-Fi authenticates with the domain account. Devices that saved the old
password keep sending it, fail, and can even lock the account after repeated attempts.

## Resolution steps
1. Check whether the account is now locked; if so, unlock it first.
2. On each device that uses the corporate Wi-Fi (laptop, phone, tablet), forget the
   network.
3. Reconnect and enter the new password.
4. If a phone keeps locking the account, turn its Wi-Fi off until it has been updated.

## Warnings
Do not move the user to the guest network as a fix; they lose access to internal systems.

## Key facts
- Corporate Wi-Fi uses the domain account, so a password change breaks saved Wi-Fi credentials.
- Devices with the old saved password can lock the domain account.
- Forgetting the network on every device and reconnecting with the new password fixes it.
