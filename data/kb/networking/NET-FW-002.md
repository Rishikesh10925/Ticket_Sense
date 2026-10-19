---
id: NET-FW-002
department: Networking
topic: net-firewall
title: Work website blocked by the web proxy
updated: '2026-08-05'
served: true
author: R
reviewer: null
legacy: proxy-blocking-site
---

## Symptom
A website needed for work shows the company's proxy block page, while other sites work.

## Cause
The web proxy blocks sites by content category. Many blocks are not aimed at that site:
it is uncategorised or sits in a category such as file sharing.

## Resolution steps
1. Get the exact address and the category shown on the block page, plus the business
   reason the site is needed.
2. If the site is clearly in the wrong category, request recategorisation from the
   security team.
3. Otherwise raise an allow-list request with the domain and justification through the
   change process.
4. Tell the user how long approval normally takes.

## Warnings
Never tell users to bypass the proxy (personal hotspot, unapproved VPN or browser
extension) to reach a blocked site.

## Key facts
- The proxy blocks by content category, not usually by specific site.
- The block page shows the category that caused the block.
- Miscategorised sites are recategorised; others need an allow-list request.
