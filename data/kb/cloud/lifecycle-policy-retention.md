# Object Storage Lifecycle / Retention Policy

**Department:** Cloud

## Issue
Question or request about how long objects are kept in a storage bucket
before being archived or deleted, or a request to change that behavior.

## Resolution
1. Check the bucket's configured lifecycle rules for existing
   transition/expiration policies before assuming none exist.
2. Retention/deletion policy changes must align with the data classification
   of what's stored — confirm with the data owner before changing retention
   on anything containing business records.
3. Changes to lifecycle rules apply going forward only; they do not
   retroactively restore or re-evaluate objects already transitioned/deleted
   under the previous rule.
4. Document the approved retention period and requester in the ticket for
   audit purposes.

## Notes
Never shorten a retention period on a bucket without confirming there's no
compliance or legal hold requirement on that data.
