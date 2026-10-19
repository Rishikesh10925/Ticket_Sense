# S3 Access Denied Error

**Department:** Cloud

## Issue
Application or user receives "Access Denied" when trying to read or write
an object in an S3 bucket that they expect to have access to.

## Resolution
1. Confirm the exact bucket, key/prefix, and action (GetObject, PutObject,
   ListBucket) that failed — Access Denied is intentionally generic and
   doesn't distinguish IAM vs. bucket policy vs. ACL causes.
2. Check the caller's IAM policy for an explicit `Deny` on that action —
   explicit denies always win regardless of any `Allow` elsewhere.
3. Check the bucket policy itself for restrictions (e.g., VPC endpoint
   conditions, source IP restrictions) that could block an otherwise
   correctly-permissioned caller.
4. If the bucket has "Block Public Access" enabled (expected for almost all
   buckets), confirm the request isn't relying on public/anonymous access.

## Notes
"Access Denied" and "does not exist" look similar in some SDKs when the
caller lacks `ListBucket` — don't assume the object is missing until access
is confirmed separately.
