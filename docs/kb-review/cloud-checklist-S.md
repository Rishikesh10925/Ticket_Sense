# Fact-check checklist: CLOUD (12 articles, reviewer S)

For each article: open it, click each term, confirm the article uses it correctly.
All correct ➜ set `reviewer: S` in the article. Something wrong ➜ note it here and tell Claude.
Values described as *this organisation's* policy (limits, approvals) are fictional company rules:
they cannot be looked up, only checked for being stated as policy rather than as a vendor default.
⭐ = check first (flagged as risky). ⬜ = not checked. 🤖 = AI-checked only (still needs a human). ✅ = human-reviewed.

## ⬜ CLD-ENV-001: Request for a new cloud environment
File: [data/kb/cloud/CLD-ENV-001.md](../../data/kb/cloud/CLD-ENV-001.md) · author A

**Look up:** (no technical terms; check the steps make sense)

**Key facts to confirm:**
- [ ] New environments are created only from the landing-zone template.
- [ ] Cost-centre, owner and environment tags are applied at creation.
- [ ] Teams get least-privilege access by default.

Notes: 

## ⬜ CLD-ENV-002: Managed database refusing new connections
File: [data/kb/cloud/CLD-ENV-002.md](../../data/kb/cloud/CLD-ENV-002.md) · author A

**Look up:** (no technical terms; check the steps make sense)

**Key facts to confirm:**
- [ ] "Too many connections" means the database reached its maximum connections setting.
- [ ] Connection leaks after a deployment are a common cause.
- [ ] Leaks are fixed before the database is resized.

Notes: 

## ⬜ CLD-ENV-003: Request for a new managed database
File: [data/kb/cloud/CLD-ENV-003.md](../../data/kb/cloud/CLD-ENV-003.md) · author A

**Look up:** (no technical terms; check the steps make sense)

**Key facts to confirm:**
- [ ] Production databases are deployed across two availability zones.
- [ ] Automated backups and encryption at rest are mandatory.
- [ ] Databases sit in private subnets, reachable only from the application's security group.

Notes: 

## ⬜ CLD-ENV-004: Decommission a cloud environment
File: [data/kb/cloud/CLD-ENV-004.md](../../data/kb/cloud/CLD-ENV-004.md) · author A

**Look up:** (no technical terms; check the steps make sense)

**Key facts to confirm:**
- [ ] Decommissioning needs confirmation from the owner and the cost-centre manager.
- [ ] Final snapshots are taken where data retention requires them.
- [ ] Accounts and projects are closed by the platform team.

Notes: 

## ⬜ CLD-LB-001: Load balancer marks servers unhealthy
File: [data/kb/cloud/CLD-LB-001.md](../../data/kb/cloud/CLD-LB-001.md) · author A

**Look up:** (no technical terms; check the steps make sense)

**Key facts to confirm:**
- [ ] Health checks fail when the path does not return the expected status code in time.
- [ ] Calling the health check path directly on the server isolates application from network problems.
- [ ] Servers flapping between healthy and unhealthy usually lack CPU or memory.

Notes: 

## ⬜ CLD-LB-002: TLS certificate about to expire
File: [data/kb/cloud/CLD-LB-002.md](../../data/kb/cloud/CLD-LB-002.md) · author A

**Look up:** (no technical terms; check the steps make sense)

**Key facts to confirm:**
- [ ] Managed certificates renew automatically only while DNS validation still works.
- [ ] A renewed certificate must be installed on every endpoint that uses it.
- [ ] An expired production certificate is a priority-1 incident.

Notes: 

## ⬜ CLD-LB-003: Website returns 502 or 503 from the load balancer
File: [data/kb/cloud/CLD-LB-003.md](../../data/kb/cloud/CLD-LB-003.md) · author A

**Look up:** (no technical terms; check the steps make sense)

**Key facts to confirm:**
- [ ] 503 from the load balancer means no healthy servers are available.
- [ ] 502 means a server closed the connection or returned an invalid response.
- [ ] 504 means the server did not respond within the load balancer timeout.

Notes: 

## ⬜ CLD-LB-004: New service needs a company domain name
File: [data/kb/cloud/CLD-LB-004.md](../../data/kb/cloud/CLD-LB-004.md) · author A

**Look up:** (no technical terms; check the steps make sense)

**Key facts to confirm:**
- [ ] A company name for a service needs a DNS record and a matching certificate.
- [ ] Load balancers are referenced by alias records, never by IP address.
- [ ] Certificates for company names are validated through DNS.

Notes: 

## ⬜ CLD-VM-001: Cannot SSH into a cloud virtual machine
File: [data/kb/cloud/CLD-VM-001.md](../../data/kb/cloud/CLD-VM-001.md) · author A

**Look up:** (no technical terms; check the steps make sense)

**Key facts to confirm:**
- [ ] An SSH timeout points to a network block such as a security group rule.
- [ ] A refused connection or failed authentication points to the key or SSH configuration.
- [ ] Private-subnet machines are reached through the bastion host or VPN.
- [ ] A failed system status check is fixed by stopping and starting the instance.

Notes: 

## ⬜ CLD-VM-002: Restore a disk or server from a snapshot
File: [data/kb/cloud/CLD-VM-002.md](../../data/kb/cloud/CLD-VM-002.md) · author A

**Look up:** (no technical terms; check the steps make sense)

**Key facts to confirm:**
- [ ] Restores go to a new resource by default, not over the original.
- [ ] Data changed after the snapshot time is not in the restored copy.
- [ ] The original is kept until the restored copy is verified by the owner.

Notes: 

## ⬜ CLD-VM-003: Virtual machine disk is full
File: [data/kb/cloud/CLD-VM-003.md](../../data/kb/cloud/CLD-VM-003.md) · author A

**Look up:** [growpart](https://www.google.com/search?q=AWS+growpart+site%3Adocs.aws.amazon.com) · [resize2fs](https://www.google.com/search?q=AWS+resize2fs+site%3Adocs.aws.amazon.com) · [xfs_growfs](https://www.google.com/search?q=AWS+xfs_growfs+site%3Adocs.aws.amazon.com)

**Key facts to confirm:**
- [ ] Growing a cloud volume does not grow the file system automatically.
- [ ] The partition is extended with growpart and the file system with resize2fs or xfs_growfs.
- [ ] A snapshot is taken before resizing a volume.

Notes: 

## ⬜ CLD-VM-004: Development server stopped overnight
File: [data/kb/cloud/CLD-VM-004.md](../../data/kb/cloud/CLD-VM-004.md) · author A

**Look up:** (no technical terms; check the steps make sense)

**Key facts to confirm:**
- [ ] Development and test machines are stopped outside working hours by the instance scheduler.
- [ ] The machine's schedule tag decides when it is stopped.
- [ ] Data on instance-store disks is lost when the machine stops.

Notes: 

