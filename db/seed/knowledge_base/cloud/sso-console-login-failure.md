# SSO Login Failure to Cloud Console

**Department:** Cloud

## Issue
User cannot log into the cloud provider console via single sign-on; gets
redirected back to the login page or receives an identity provider error.

## Resolution
1. Confirm the user's corporate account itself is active and not locked
   (same account used for other SSO-linked apps) — if other SSO apps also
   fail for them, this is an identity provider issue, not cloud-specific.
2. Confirm the user is actually assigned to the cloud console application in
   the identity provider — a missing app assignment produces a similar
   redirect-loop symptom to a genuine auth failure.
3. Check for a role/permission set mapping issue if the user authenticates
   successfully but lands on an "access denied" or blank console.
4. Clear browser cookies/cache or try an incognito window to rule out a
   stale cached session before escalating.

## Notes
If multiple users are affected simultaneously, treat as an identity provider
or SSO integration outage rather than troubleshooting individually.
