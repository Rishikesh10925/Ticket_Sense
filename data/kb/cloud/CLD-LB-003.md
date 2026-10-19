---
id: CLD-LB-003
department: Cloud
topic: cloud-traffic
title: Website returns 502 or 503 from the load balancer
updated: '2025-10-07'
served: true
author: A
reviewer: null
---

## Symptom
Users get "502 Bad Gateway", "503 Service Unavailable" or "504 Gateway Timeout" from an
application behind a cloud load balancer.

## Cause
The code shows where it failed. 503 means the load balancer has no healthy servers. 502
means a server closed the connection or sent an invalid response. 504 means the server
did not answer within the load balancer's timeout.

## Resolution steps
1. Note the exact error code and when it started.
2. For 503, check the target group: if no servers are healthy, follow the unhealthy-server
   article.
3. For 502, check the application logs on the servers for crashes or restarts at that time.
4. For 504, check for slow requests or a dependency (database, external API) that slowed
   down.
5. Send the findings to the application's owning team.

## Warnings
Do not raise the load balancer timeout to hide 504 errors without the owning team.

## Key facts
- 503 from the load balancer means no healthy servers are available.
- 502 means a server closed the connection or returned an invalid response.
- 504 means the server did not respond within the load balancer timeout.
