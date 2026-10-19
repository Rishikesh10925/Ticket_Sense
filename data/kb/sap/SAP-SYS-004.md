---
id: SAP-SYS-004
department: SAP
topic: sap-system
title: Wrong date or number format in SAP
updated: '2026-03-04'
served: true
author: S
reviewer: null
---

## Symptom
SAP shows dates as month/day/year instead of day/month/year, or uses a comma instead of a
decimal point, so amounts look ten or a thousand times wrong in downloads.

## Cause
Date and decimal formats are personal settings stored in the user's master record; they
may differ from Windows regional settings.

## Resolution steps
1. Open transaction SU3 (own user data) and go to the Defaults tab.
2. Choose the correct decimal notation and date format.
3. Save, then log off and log on again so the new settings apply.
4. Re-export any spreadsheet downloads made with the wrong format.

## Warnings
The formats affect only how values are displayed and exported, not the stored data; do
not correct postings because of a display format.

## Key facts
- Date and decimal formats are set per user in SU3 on the Defaults tab.
- New formats apply after logging off and on again.
- Display formats do not change the stored data.
