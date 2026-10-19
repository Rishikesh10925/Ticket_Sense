# Cloud Storage Quota Exceeded

**Department:** Cloud

## Issue
Application or backup job fails with a storage quota/limit error, or writes
start failing while reads continue to work.

## Resolution
1. Confirm which quota was hit — account-level service quota, bucket/volume
   size limit, or a cost-control budget alert that's blocking further spend.
2. For a genuine size limit, check whether old/unneeded data can be archived
   or deleted (per the relevant retention policy) before requesting a quota
   increase.
3. Service quota increases go through the standard cloud provider request
   process and are not instant — flag the urgency clearly if this is
   actively blocking production.
4. If this is a recurring pattern (quota creeping up steadily), flag for a
   capacity-planning review rather than repeatedly requesting incremental
   increases.

## Notes
Don't request the largest possible quota "to be safe" — oversized quotas
make runaway cost or data growth harder to catch early.
