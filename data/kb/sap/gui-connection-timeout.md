# SAP GUI Connection Timeout

**Department:** SAP

## Issue
SAP GUI hangs on "Connecting to server..." and eventually times out before
reaching the login screen.

## Resolution
1. Confirm the user can reach the application server on the network
   (VPN connected if working remotely — see Networking KB for VPN issues).
2. Check the SAP Logon Pad connection entry: Application Server, Instance
   Number, and System ID must match the current production values (these
   occasionally change after a system refresh).
3. Clear the local SAP GUI cache: close GUI, delete the `%APPDATA%\SAP\SAP
   GUI\Cache` folder, reopen.
4. If the issue is server-side (affects multiple users), escalate to Basis —
   this is not a client-fixable issue.

## Notes
A single affected user usually means a client config or VPN issue; multiple
users reporting at once means the application server is likely down.
