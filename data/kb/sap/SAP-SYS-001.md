---
id: SAP-SYS-001
department: SAP
topic: sap-system
title: SAP GUI cannot connect to the server
updated: '2026-09-21'
served: true
author: S
reviewer: null
legacy: gui-connection-timeout
---

## Symptom
SAP GUI hangs on "Connecting" after the user selects a system in SAP Logon and then
fails with a connection or timeout error before the logon screen appears.

## Cause
The user's machine cannot reach the application server: no VPN when working remotely, a
wrong or outdated system entry in SAP Logon, or the server itself is down.

## Resolution steps
1. If the user works remotely, confirm the VPN is connected; see the Networking VPN
   articles if it is not.
2. Ask whether colleagues can connect to the same system. If several users are affected,
   the server is probably down: escalate to Basis at once.
3. Check the system entry in SAP Logon: application server, instance number and system
   ID must match the values published by Basis. Entries can change after a system refresh.
4. Test that the dispatcher port is reachable. SAP GUI connects to port 32 followed by
   the instance number (3200 for instance 00).
5. If only this user is affected and the entry is correct, reinstall or update SAP GUI
   from the software centre.

## Warnings
Do not change the central SAP Logon landscape file for one user; it is managed by Basis.

## Key facts
- Several users unable to connect at once points to a server problem for Basis.
- SAP GUI connects to the dispatcher on port 32 plus the instance number (3200 for instance 00).
- Remote users need the VPN connected before SAP GUI can reach the server.
