# Fact-check checklist: CLOUD (12 articles, reviewer A)

For each article: open it, click each term, confirm the article uses it correctly.
All correct ➜ set `reviewer: A` in the article. Something wrong ➜ note it here and tell Claude.
Values described as *this organisation's* policy (limits, approvals) are fictional company rules:
they cannot be looked up, only checked for being stated as policy rather than as a vendor default.
⭐ = check first (flagged as risky). ⬜ = not checked. 🤖 = AI-checked only (still needs a human). ✅ = human-reviewed.

## ⬜ CLD-COST-001: Cloud cost anomaly alert
File: [data/kb/cloud/CLD-COST-001.md](../../data/kb/cloud/CLD-COST-001.md) · author R

**Look up:** [COST](https://www.google.com/search?q=AWS+COST+site%3Adocs.aws.amazon.com)

**Key facts to confirm:**
- [ ] A cost breakdown by service usually points to the cause at once.
- [ ] Owners are identified from resource tags.
- [ ] Resources are stopped only after the owner confirms they are unintended.

Notes: 

## ⬜ CLD-COST-002: Costs missing from the team's cost report
File: [data/kb/cloud/CLD-COST-002.md](../../data/kb/cloud/CLD-COST-002.md) · author R

**Look up:** [COST](https://www.google.com/search?q=AWS+COST+site%3Adocs.aws.amazon.com)

**Key facts to confirm:**
- [ ] Costs are attributed to teams through the cost-centre tag.
- [ ] A new tag key must be activated as a cost allocation tag before it appears in cost reports.
- [ ] Tags and activation do not apply retroactively to past costs.

Notes: 

## ⬜ CLD-COST-003: Unexpected data transfer charges
File: [data/kb/cloud/CLD-COST-003.md](../../data/kb/cloud/CLD-COST-003.md) · author R

**Look up:** [COST](https://www.google.com/search?q=AWS+COST+site%3Adocs.aws.amazon.com)

**Key facts to confirm:**
- [ ] Data leaving the cloud to the internet is charged; inbound data is not.
- [ ] Traffic through a NAT gateway pays an extra per-gigabyte processing charge.
- [ ] Traffic between availability zones is also charged.

Notes: 

## ⬜ CLD-COST-004: Project budget alert received
File: [data/kb/cloud/CLD-COST-004.md](../../data/kb/cloud/CLD-COST-004.md) · author R

**Look up:** [COST](https://www.google.com/search?q=AWS+COST+site%3Adocs.aws.amazon.com)

**Key facts to confirm:**
- [ ] Budget alerts can be on actual or on forecast spend.
- [ ] Budget alerts only notify; they do not stop resources.
- [ ] Budget changes are requested from finance by the project owner.

Notes: 

## ⬜ CLD-IAM-001: Request for additional cloud permissions
File: [data/kb/cloud/CLD-IAM-001.md](../../data/kb/cloud/CLD-IAM-001.md) · author R

**Look up:** [s3:PutObject](https://www.google.com/search?q=AWS+s3%3APutObject+site%3Adocs.aws.amazon.com)

**Key facts to confirm:**
- [ ] The authorization error names the denied action and resource.
- [ ] Permissions are granted through groups or roles, not policies on individual users.
- [ ] Requests are scoped to specific actions and resources (least privilege).
- [ ] Temporary access carries an expiry or review date.

Notes: 

## ⬜ CLD-IAM-002: Single sign-on to the cloud console fails
File: [data/kb/cloud/CLD-IAM-002.md](../../data/kb/cloud/CLD-IAM-002.md) · author R

**Look up:** (no technical terms; check the steps make sense)

**Key facts to confirm:**
- [ ] If all single sign-on apps fail, the problem is the corporate account, not the cloud.
- [ ] A user not assigned to the cloud app in the identity provider gets a redirect loop.
- [ ] Signing in but seeing access denied means no role is mapped to the user's groups.

Notes: 

## ⬜ CLD-IAM-003: Cloud access key exposed or committed to a repository
File: [data/kb/cloud/CLD-IAM-003.md](../../data/kb/cloud/CLD-IAM-003.md) · author R

**Look up:** (no technical terms; check the steps make sense)

**Key facts to confirm:**
- [ ] An exposed access key is deactivated immediately, before anything else.
- [ ] A key that was pushed or shared is compromised even if the commit is removed.
- [ ] Roles with temporary credentials are preferred over long-lived access keys.
- [ ] Activity logs are reviewed for use of the exposed key.

Notes: 

## ⬜ CLD-IAM-004: Lost phone for cloud console multi-factor sign-in
File: [data/kb/cloud/CLD-IAM-004.md](../../data/kb/cloud/CLD-IAM-004.md) · author R

**Look up:** (no technical terms; check the steps make sense)

**Key facts to confirm:**
- [ ] Console multi-factor is managed in the corporate identity provider.
- [ ] A multi-factor reset needs identity verification first.
- [ ] A lost phone is also reported to security as a lost device.

Notes: 

## ⬜ CLD-STO-001: Access denied on an object storage bucket
File: [data/kb/cloud/CLD-STO-001.md](../../data/kb/cloud/CLD-STO-001.md) · author R

**Look up:** (no technical terms; check the steps make sense)

**Key facts to confirm:**
- [ ] An explicit deny always overrides an allow.
- [ ] Bucket policies can block a correctly permissioned caller through conditions.
- [ ] Without list permission, a missing object can return access denied.

Notes: 

## ⬜ CLD-STO-002: Writes fail because a storage quota is reached
File: [data/kb/cloud/CLD-STO-002.md](../../data/kb/cloud/CLD-STO-002.md) · author R

**Look up:** (no technical terms; check the steps make sense)

**Key facts to confirm:**
- [ ] Quota errors can come from service quotas, size limits or budget controls.
- [ ] Retention-policy clean-up is checked before requesting more capacity.
- [ ] Service quota increases are not instant.

Notes: 

## ⬜ CLD-STO-003: How long files are kept in a bucket
File: [data/kb/cloud/CLD-STO-003.md](../../data/kb/cloud/CLD-STO-003.md) · author R

**Look up:** (no technical terms; check the steps make sense)

**Key facts to confirm:**
- [ ] Lifecycle rules transition or delete objects after a number of days.
- [ ] Retention changes need the data owner's approval, and compliance for business records.
- [ ] Lifecycle rule changes do not restore objects already deleted.

Notes: 

## ⬜ CLD-STO-004: Shared download link to a bucket file has expired
File: [data/kb/cloud/CLD-STO-004.md](../../data/kb/cloud/CLD-STO-004.md) · author R

**Look up:** (no technical terms; check the steps make sense)

**Key facts to confirm:**
- [ ] Pre-signed URLs expire at the lifetime set when they were created.
- [ ] A pre-signed URL never outlives the credentials that signed it.
- [ ] The maximum lifetime of a pre-signed URL is seven days.

Notes: 

