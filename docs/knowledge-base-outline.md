# Knowledge-base article outline

Week 1 outline (Shivaganesh) of the synthetic knowledge-base articles to be authored
across TicketSense's five target departments, per the project blueprint's dataset
strategy (a self-authored knowledge base is the source of department-scoped RAG
evidence, since a real company's confidential knowledge base isn't available). This is
an **outline only** — titles and one-line summaries, no article content yet. Authoring
the first batch (SAP and Networking) is Week 2 scope.

Four of the five departments (SAP, Networking, Cloud, HR) reuse the article set an
earlier prototype had already authored and seeded (recovered from git history — 12
articles each, 48 total, matching the row count `architecture.md`'s "Known limitation"
section references). **Database is a new department outline**, not present in that
earlier version, added here to reach the blueprint's five target departments.

## SAP (12)

| Article | Covers |
|---|---|
| `me023-error-goods-receipt` | Fixing SAP error ME023 on purchase-order/goods-receipt creation |
| `po-blocked-for-approval` | Purchase orders stuck in a blocked-for-approval state |
| `locked-user-account` | Unlocking a locked SAP user account |
| `missing-tcode-authorization` | Requesting authorization for a missing transaction code |
| `material-locked-by-user` | Resolving a material record locked by another user |
| `idoc-status-51` | Diagnosing and reprocessing a failed IDoc (status 51) |
| `batch-job-stuck` | Investigating a background batch job stuck in "running" |
| `gui-connection-timeout` | SAP GUI connection timeouts to the application server |
| `incorrect-exchange-rate-fi` | Correcting an incorrect exchange rate in FI postings |
| `number-range-exhausted` | Requesting a new number range interval once exhausted |
| `print-output-missing-sp01` | Missing print output in SP01 spool requests |
| `short-dump-st22` | Reading and triaging an ABAP short dump in ST22 |

## Networking (12)

| Article | Covers |
|---|---|
| `vpn-not-connecting` | Client VPN failing to establish a connection |
| `site-to-site-vpn-down` | Site-to-site VPN tunnel down between offices |
| `wifi-dropping-office` | Intermittent office Wi-Fi disconnects |
| `guest-wifi-access` | Provisioning guest Wi-Fi access |
| `no-ip-dhcp-limited` | Device stuck on a limited/APIPA address, no DHCP lease |
| `dns-internal-hostname-fail` | Internal hostnames failing to resolve |
| `proxy-blocking-site` | Corporate proxy blocking a legitimate site |
| `firewall-port-request` | Requesting a firewall port/rule change |
| `new-desk-vlan-port` | Provisioning a new desk's switch port/VLAN |
| `switch-port-error-disabled` | Re-enabling a switch port stuck in err-disabled |
| `mapped-drive-inaccessible` | Mapped network drive inaccessible after a password change |
| `video-call-latency` | High latency/jitter on video calls |

## Cloud (12)

| Article | Covers |
|---|---|
| `s3-access-denied` | Diagnosing S3 access-denied errors |
| `iam-permission-request` | Requesting an IAM permission/role change |
| `ec2-ssh-unreachable` | EC2 instance unreachable over SSH |
| `sso-console-login-failure` | SSO login failures to the cloud console |
| `database-connection-timeout` | Application-to-database connection timeouts in the cloud |
| `load-balancer-health-check-failing` | Load balancer target failing health checks |
| `storage-quota-exceeded` | Storage quota exceeded on a managed volume |
| `snapshot-restore-request` | Requesting a snapshot restore |
| `lifecycle-policy-retention` | Configuring object lifecycle/retention policy |
| `cost-spike-alert` | Investigating an unexpected cost spike |
| `new-environment-provisioning` | Requesting a new environment be provisioned |
| `tls-certificate-expiring` | Renewing a soon-to-expire TLS certificate |

## Database (12 — new)

| Article | Covers |
|---|---|
| `connection-pool-exhausted` | Application errors from an exhausted DB connection pool |
| `deadlock-detected-rollback` | Diagnosing a deadlock-triggered transaction rollback |
| `backup-restore-request` | Requesting a database backup or point-in-time restore |
| `slow-query-performance` | Triaging a slow-running query |
| `replication-lag-alert` | Investigating replica lag past an alert threshold |
| `disk-space-critical` | Database volume nearing/at disk-space capacity |
| `schema-migration-failed` | A failed schema migration and how to recover |
| `db-access-permission-request` | Requesting read/write access to a schema or table |
| `index-corruption-repair` | Detecting and repairing a corrupted index |
| `failover-not-triggering` | Automated failover not triggering as expected |
| `db-connection-timeout-app` | Application-side connection timeouts to the database |
| `orphaned-lock-blocking-table` | Clearing an orphaned lock blocking a table |

## HR (12)

| Article | Covers |
|---|---|
| `apply-for-leave` | How to submit a leave request |
| `leave-policy-overview` | Summary of the leave policy |
| `wfh-hybrid-policy` | Work-from-home/hybrid policy overview |
| `resignation-notice-period` | Resignation process and notice period |
| `onboarding-checklist` | New-hire onboarding checklist |
| `timesheet-submission` | How to submit a timesheet |
| `payroll-payslip-access` | Accessing payslips and payroll records |
| `benefits-enrollment-window` | Benefits enrollment window and process |
| `insurance-claim-process` | Filing an insurance claim |
| `expense-reimbursement` | Submitting an expense reimbursement |
| `performance-review-cycle` | Performance review cycle and timelines |
| `public-holiday-calendar` | Public holiday calendar for the year |

## Notes for Week 2 authoring

- Each article should stay short (roughly one incident/request per article, matching the
  granularity above) so retrieval returns a specific, citable chunk rather than a broad
  policy document.
- SAP and Networking are the Week 2 authoring priority per the roadmap; Cloud, Database,
  and HR follow.
- Once authored, these feed [architecture.md](architecture.md)'s embedding pipeline
  (`sentence-transformers/all-MiniLM-L6-v2`, 384-dim, stored in `pgvector`) — not built
  yet.
