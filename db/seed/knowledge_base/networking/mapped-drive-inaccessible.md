# Mapped Network Drive Inaccessible

**Department:** Networking

## Issue
A previously working mapped network drive shows as disconnected (red X) or
returns "network path not found" when opened.

## Resolution
1. Confirm the user is connected to the corporate network or VPN — mapped
   drives to internal file servers aren't reachable from the open internet.
2. Try accessing the share directly via UNC path (`\\server\share`) to
   confirm whether the issue is the mapping itself or the underlying share.
3. If the UNC path also fails, check whether the file server is up
   (ask if other users on the same server are affected) before troubleshooting
   the individual machine further.
4. If only the mapping is broken, remove and re-add the mapped drive rather
   than trying to repair it.

## Notes
Password changes can break saved credentials on mapped drives — if the user
recently reset their password, re-enter credentials on reconnect.
