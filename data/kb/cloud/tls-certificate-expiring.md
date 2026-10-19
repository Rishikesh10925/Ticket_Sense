# TLS Certificate Expiring Warning

**Department:** Cloud

## Issue
Monitoring alert fires that a TLS/SSL certificate for a service or domain
is approaching expiration.

## Resolution
1. Confirm which certificate and endpoint the alert refers to, and whether
   it's managed by an automated certificate service (auto-renewing) or
   manually issued.
2. For auto-renewing certificates, check why renewal hasn't happened
   automatically — usually a failed domain validation or a DNS record
   change that broke the validation path.
3. For manually managed certificates, initiate reissuance well before
   expiry and update the certificate on all endpoints/load balancers using
   it — missing one endpoint is the most common cause of a "renewed but
   still expired" complaint.
4. After renewal, verify the new certificate is actually being served
   (check the expiry date returned by the endpoint itself, not just the
   certificate store).

## Notes
An expired certificate causing a production outage is a P1 — don't wait for
the standard change window to renew a cert that's already past expiry.
