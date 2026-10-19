---
id: NET-FW-003
department: Networking
topic: net-firewall
title: Certificate errors in a desktop tool on the office network
updated: '2025-06-03'
served: true
author: R
reviewer: null
---

## Symptom
A developer tool, command-line client or desktop app fails with an SSL or certificate
error ("unable to get local issuer certificate", "self-signed certificate in chain") on
the office network, but works at home.

## Cause
The web proxy inspects encrypted traffic and re-signs it with the company's root
certificate. Browsers trust that certificate, but some tools use their own certificate
store and do not.

## Resolution steps
1. Confirm the error appears only on the office network or VPN.
2. Point the tool at the company root certificate, which is published on the intranet
   (most tools have a setting or environment variable for a CA bundle).
3. If the tool cannot be configured, raise a request for an inspection bypass for that
   domain, with the business reason.

## Warnings
Never turn off certificate verification in the tool; it removes protection against
real interception.

## Key facts
- The proxy re-signs inspected traffic with the company root certificate.
- Tools with their own certificate store must be pointed at the company root certificate.
- Disabling certificate verification is never an acceptable fix.
