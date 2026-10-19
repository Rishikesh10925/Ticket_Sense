---
id: CLD-LB-002
department: Cloud
topic: cloud-traffic
title: TLS certificate about to expire
updated: '2026-09-24'
served: true
author: A
reviewer: null
legacy: tls-certificate-expiring
---

## Symptom
Monitoring warns that the TLS certificate of a website or API expires soon, or users
already see a certificate warning in the browser.

## Cause
Managed certificates renew automatically only if domain validation still works; a changed
or deleted DNS validation record stops renewal. Manually issued certificates must be
renewed and installed by hand on every endpoint that uses them.

## Resolution steps
1. Identify the certificate, its domain and every endpoint that uses it.
2. For a managed certificate, check its renewal status and that the DNS validation record
   still exists.
3. For a manual certificate, request a new one well before expiry and install it on all
   endpoints and load balancers.
4. Check the certificate actually served by each endpoint and its new expiry date.

## Warnings
A certificate that has already expired on a production site is a priority-1 incident; do
not wait for the normal change window.

## Key facts
- Managed certificates renew automatically only while DNS validation still works.
- A renewed certificate must be installed on every endpoint that uses it.
- An expired production certificate is a priority-1 incident.
