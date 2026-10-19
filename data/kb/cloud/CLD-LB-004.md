---
id: CLD-LB-004
department: Cloud
topic: cloud-traffic
title: New service needs a company domain name
updated: '2026-03-17'
served: true
author: A
reviewer: null
---

## Symptom
A team has a new application running behind a load balancer and wants it reachable under
a company domain name with HTTPS.

## Cause
The name needs a DNS record pointing at the load balancer and a certificate for that
name, both managed by the platform team.

## Resolution steps
1. Get the desired name, the load balancer, the environment and the owning team.
2. Request a certificate for the name; it is validated through a DNS record.
3. Ask the platform team to create an alias record that points the name at the load
   balancer.
4. Add the certificate to the load balancer's HTTPS listener and test the site with the
   new name.

## Warnings
Do not point records at a load balancer's IP addresses; they change. Use an alias record.

## Key facts
- A company name for a service needs a DNS record and a matching certificate.
- Load balancers are referenced by alias records, never by IP address.
- Certificates for company names are validated through DNS.
