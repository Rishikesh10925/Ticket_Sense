---
id: CLD-STO-004
department: Cloud
topic: cloud-storage
title: Shared download link to a bucket file has expired
updated: '2026-05-12'
served: true
author: R
reviewer: null
---

## Symptom
A partner or colleague opens a download link for a file in cloud storage and gets
"Request has expired" or access denied, although the link worked earlier.

## Cause
The link was a pre-signed URL. It works only for the lifetime set when it was created,
and never longer than the credentials used to sign it. Links signed with temporary role
credentials stop working when that session ends.

## Resolution steps
1. Confirm the link contains signature parameters (it is a pre-signed URL, not a public
   object).
2. Ask the file owner to generate a new link with an appropriate expiry.
3. For links that must last days, the owner should sign with credentials that remain
   valid for that long; the maximum lifetime is seven days.
4. For recurring sharing with a partner, recommend a proper partner-access setup instead
   of repeated links.

## Warnings
Do not make the object or bucket public to replace an expired link.

## Key facts
- Pre-signed URLs expire at the lifetime set when they were created.
- A pre-signed URL never outlives the credentials that signed it.
- The maximum lifetime of a pre-signed URL is seven days.
