# Fact-check checklist: DATABASE (24 articles, reviewer S)

For each article: open it, click each term, confirm the article uses it correctly.
All correct ➜ set `reviewer: S` in the article. Something wrong ➜ note it here and tell Claude.
Values described as *this organisation's* policy (limits, approvals) are fictional company rules:
they cannot be looked up, only checked for being stated as policy rather than as a vendor default.
⭐ = check first (flagged as risky). ⬜ = not checked. 🤖 = AI-checked only (still needs a human). ✅ = human-reviewed.

## ⬜ DB-CHG-001: Request for access to a database
File: [data/kb/database/DB-CHG-001.md](../../data/kb/database/DB-CHG-001.md) · author A

**Look up:** (no technical terms; check the steps make sense)

**Key facts to confirm:**
- [ ] Access is granted through the narrowest role that fits the request.
- [ ] Each service gets its own dedicated role.
- [ ] Grants are recorded with who, what, why and when.

Notes: 

## ⬜ DB-CHG-002: Schema migration failed halfway
File: [data/kb/database/DB-CHG-002.md](../../data/kb/database/DB-CHG-002.md) · author A

**Look up:** [CREATE INDEX
CONCURRENTLY](https://www.google.com/search?q=PostgreSQL+CREATE+INDEX%0ACONCURRENTLY+site%3Apostgresql.org%2Fdocs) · [alembic_version](https://www.google.com/search?q=PostgreSQL+alembic_version+site%3Apostgresql.org%2Fdocs) · [CREATE](https://www.google.com/search?q=PostgreSQL+CREATE+site%3Apostgresql.org%2Fdocs) · [INDEX](https://www.google.com/search?q=PostgreSQL+INDEX+site%3Apostgresql.org%2Fdocs)

**Key facts to confirm:**
- [ ] The migration version table may not match the real schema after a failure.
- [ ] Non-transactional statements like CREATE INDEX CONCURRENTLY can leave partial changes.
- [ ] The schema is brought to one consistent version before rerunning.

Notes: 

## ⬜ DB-CHG-003: Request to run a data fix in production
File: [data/kb/database/DB-CHG-003.md](../../data/kb/database/DB-CHG-003.md) · author A

**Look up:** [UPDATE](https://www.google.com/search?q=PostgreSQL+UPDATE+site%3Apostgresql.org%2Fdocs) · [DELETE](https://www.google.com/search?q=PostgreSQL+DELETE+site%3Apostgresql.org%2Fdocs) · [WHERE](https://www.google.com/search?q=PostgreSQL+WHERE+site%3Apostgresql.org%2Fdocs) · [SELECT COUNT(*)](https://www.google.com/search?q=PostgreSQL+SELECT+COUNT%28%2A%29+site%3Apostgresql.org%2Fdocs) · [SELECT](https://www.google.com/search?q=PostgreSQL+SELECT+site%3Apostgresql.org%2Fdocs) · [COUNT](https://www.google.com/search?q=PostgreSQL+COUNT+site%3Apostgresql.org%2Fdocs)

**Key facts to confirm:**
- [ ] Production data fixes need an approved change and the expected row count.
- [ ] The WHERE clause is tested with SELECT COUNT(*) before the change runs.
- [ ] Data fixes run inside a transaction and are committed only if the row count matches.

Notes: 

## ⬜ DB-CHG-004: Read-only access for reporting tools
File: [data/kb/database/DB-CHG-004.md](../../data/kb/database/DB-CHG-004.md) · author A

**Look up:** (no technical terms; check the steps make sense)

**Key facts to confirm:**
- [ ] Reporting tools connect to the read replica, not the primary.
- [ ] Analysts get the read-only reporting role.
- [ ] Access to personal data needs the data protection officer's check.

Notes: 

## ⬜ DB-CONN-001: Application runs out of database connections
File: [data/kb/database/DB-CONN-001.md](../../data/kb/database/DB-CONN-001.md) · author A

**Look up:** [max_connections](https://www.google.com/search?q=PostgreSQL+max_connections+site%3Apostgresql.org%2Fdocs) · [pg_stat_activity](https://www.google.com/search?q=PostgreSQL+pg_stat_activity+site%3Apostgresql.org%2Fdocs) · [SHOW max_connections](https://www.google.com/search?q=PostgreSQL+SHOW+max_connections+site%3Apostgresql.org%2Fdocs) · [CONN](https://www.google.com/search?q=PostgreSQL+CONN+site%3Apostgresql.org%2Fdocs) · [SHOW](https://www.google.com/search?q=PostgreSQL+SHOW+site%3Apostgresql.org%2Fdocs)

**Key facts to confirm:**
- [ ] "too many clients already" means the server reached max_connections.
- [ ] Sessions idle in transaction hold connection slots while doing no work.
- [ ] Restarting the application releases leaked connections but is only a stop-gap.

Notes: 

## ⬜ DB-CONN-002: Application times out connecting to the database
File: [data/kb/database/DB-CONN-002.md](../../data/kb/database/DB-CONN-002.md) · author A

**Look up:** [CONN](https://www.google.com/search?q=PostgreSQL+CONN+site%3Apostgresql.org%2Fdocs)

**Key facts to confirm:**
- [ ] A client working from another host does not rule out the application host's network path.
- [ ] A connect timeout set too short causes intermittent failures under load.
- [ ] Timeouts at the same time each day point to a scheduled job.

Notes: 

## ⬜ DB-CONN-003: Password authentication failed after credential rotation
File: [data/kb/database/DB-CONN-003.md](../../data/kb/database/DB-CONN-003.md) · author A

**Look up:** [CONN](https://www.google.com/search?q=PostgreSQL+CONN+site%3Apostgresql.org%2Fdocs)

**Key facts to confirm:**
- [ ] "password authentication failed" right after rotation means the application still uses the old password.
- [ ] Applications that cache secrets at start-up need a restart after rotation.
- [ ] Database passwords belong in the secrets manager, not configuration files.

Notes: 

## ⬜ DB-CONN-004: Connection rejected with no pg_hba.conf entry
File: [data/kb/database/DB-CONN-004.md](../../data/kb/database/DB-CONN-004.md) · author A

**Look up:** [pg_hba.conf](https://www.google.com/search?q=PostgreSQL+pg_hba.conf+site%3Apostgresql.org%2Fdocs) · [CONN](https://www.google.com/search?q=PostgreSQL+CONN+site%3Apostgresql.org%2Fdocs)

**Key facts to confirm:**
- [ ] "no pg_hba.conf entry" means no rule allows that host, user, database and SSL setting.
- [ ] The error message names the client address, user and database.
- [ ] pg_hba.conf changes are made by the DBA team through a change request.

Notes: 

## ⬜ DB-HA-001: Read replica lagging behind
File: [data/kb/database/DB-HA-001.md](../../data/kb/database/DB-HA-001.md) · author A

**Look up:** (no technical terms; check the steps make sense)

**Key facts to confirm:**
- [ ] Lag caused by a write burst usually recovers after the burst.
- [ ] Long-running queries on a replica can delay replay.
- [ ] Read-your-own-writes features must read from the primary.

Notes: 

## ⬜ DB-HA-002: Automatic failover did not happen
File: [data/kb/database/DB-HA-002.md](../../data/kb/database/DB-HA-002.md) · author A

**Look up:** (no technical terms; check the steps make sense)

**Key facts to confirm:**
- [ ] A health check that only tests the port can keep a broken primary looking healthy.
- [ ] Service is restored first by promoting the standby manually.
- [ ] Promoting while the old primary still accepts writes causes split brain.

Notes: 

## ⬜ DB-HA-003: Writes fail with read-only transaction error
File: [data/kb/database/DB-HA-003.md](../../data/kb/database/DB-HA-003.md) · author A

**Look up:** [INSERT](https://www.google.com/search?q=PostgreSQL+INSERT+site%3Apostgresql.org%2Fdocs) · [UPDATE](https://www.google.com/search?q=PostgreSQL+UPDATE+site%3Apostgresql.org%2Fdocs) · [DELETE](https://www.google.com/search?q=PostgreSQL+DELETE+site%3Apostgresql.org%2Fdocs)

**Key facts to confirm:**
- [ ] "read-only transaction" errors mean the application is connected to a replica or standby.
- [ ] After a failover, the old primary can become a standby.
- [ ] Applications should use the cluster's write endpoint, which follows the primary.

Notes: 

## ⬜ DB-HA-004: Inactive replication slot
File: [data/kb/database/DB-HA-004.md](../../data/kb/database/DB-HA-004.md) · author A

**Look up:** [pg_replication_slots](https://www.google.com/search?q=PostgreSQL+pg_replication_slots+site%3Apostgresql.org%2Fdocs) · [active = false](https://www.google.com/search?q=PostgreSQL+active+%3D+false+site%3Apostgresql.org%2Fdocs) · [pg_drop_replication_slot](https://www.google.com/search?q=PostgreSQL+pg_drop_replication_slot+site%3Apostgresql.org%2Fdocs)

**Key facts to confirm:**
- [ ] An inactive replication slot makes the primary keep WAL indefinitely.
- [ ] pg_replication_slots shows which slots are inactive.
- [ ] Dropping a slot used by a live replica forces a rebuild of that replica.

Notes: 

## ⬜ DB-LOCK-001: Transaction fails with deadlock detected
File: [data/kb/database/DB-LOCK-001.md](../../data/kb/database/DB-LOCK-001.md) · author A

**Look up:** [LOCK](https://www.google.com/search?q=PostgreSQL+LOCK+site%3Apostgresql.org%2Fdocs)

**Key facts to confirm:**
- [ ] A deadlock happens when two transactions lock the same rows in opposite order.
- [ ] PostgreSQL cancels one transaction; the application must retry it.
- [ ] The database log shows both statements in the deadlock.
- [ ] Locking rows in a consistent order prevents deadlocks.

Notes: 

## ⬜ DB-LOCK-002: Queries blocked by an idle session holding a lock
File: [data/kb/database/DB-LOCK-002.md](../../data/kb/database/DB-LOCK-002.md) · author A

**Look up:** [pg_blocking_pids()](https://www.google.com/search?q=PostgreSQL+pg_blocking_pids%28%29+site%3Apostgresql.org%2Fdocs) · [pg_stat_activity](https://www.google.com/search?q=PostgreSQL+pg_stat_activity+site%3Apostgresql.org%2Fdocs) · [pg_terminate_backend(pid)](https://www.google.com/search?q=PostgreSQL+pg_terminate_backend%28pid%29+site%3Apostgresql.org%2Fdocs) · [LOCK](https://www.google.com/search?q=PostgreSQL+LOCK+site%3Apostgresql.org%2Fdocs)

**Key facts to confirm:**
- [ ] A session "idle in transaction" keeps its locks until it ends.
- [ ] pg_blocking_pids() identifies the session blocking a query.
- [ ] pg_terminate_backend ends the session and releases its locks.

Notes: 

## ⬜ DB-LOCK-003: Statement cancelled due to statement or lock timeout
File: [data/kb/database/DB-LOCK-003.md](../../data/kb/database/DB-LOCK-003.md) · author A

**Look up:** [statement_timeout](https://www.google.com/search?q=PostgreSQL+statement_timeout+site%3Apostgresql.org%2Fdocs) · [lock_timeout](https://www.google.com/search?q=PostgreSQL+lock_timeout+site%3Apostgresql.org%2Fdocs) · [LOCK](https://www.google.com/search?q=PostgreSQL+LOCK+site%3Apostgresql.org%2Fdocs)

**Key facts to confirm:**
- [ ] statement_timeout cancels queries that run too long.
- [ ] lock_timeout cancels statements that wait too long for a lock.
- [ ] A longer timeout is set per session for a legitimate job, never database-wide.

Notes: 

## ⬜ DB-LOCK-004: Schema change hangs and blocks the whole table
File: [data/kb/database/DB-LOCK-004.md](../../data/kb/database/DB-LOCK-004.md) · author A

**Look up:** [ALTER TABLE](https://www.google.com/search?q=PostgreSQL+ALTER+TABLE+site%3Apostgresql.org%2Fdocs) · [lock_timeout](https://www.google.com/search?q=PostgreSQL+lock_timeout+site%3Apostgresql.org%2Fdocs) · [LOCK](https://www.google.com/search?q=PostgreSQL+LOCK+site%3Apostgresql.org%2Fdocs) · [ALTER](https://www.google.com/search?q=PostgreSQL+ALTER+site%3Apostgresql.org%2Fdocs) · [TABLE](https://www.google.com/search?q=PostgreSQL+TABLE+site%3Apostgresql.org%2Fdocs)

**Key facts to confirm:**
- [ ] ALTER TABLE needs an exclusive lock on the table.
- [ ] A waiting ALTER TABLE blocks every new query on that table behind it.
- [ ] Migrations set a short lock_timeout so they fail fast instead of blocking.

Notes: 

## ⬜ DB-PERF-001: A query has become slow
File: [data/kb/database/DB-PERF-001.md](../../data/kb/database/DB-PERF-001.md) · author A

**Look up:** [pg_stat_statements](https://www.google.com/search?q=PostgreSQL+pg_stat_statements+site%3Apostgresql.org%2Fdocs) · [EXPLAIN (ANALYZE, BUFFERS)](https://www.google.com/search?q=PostgreSQL+EXPLAIN+%28ANALYZE%2C+BUFFERS%29+site%3Apostgresql.org%2Fdocs) · [ANALYZE](https://www.google.com/search?q=PostgreSQL+ANALYZE+site%3Apostgresql.org%2Fdocs) · [PERF](https://www.google.com/search?q=PostgreSQL+PERF+site%3Apostgresql.org%2Fdocs)

**Key facts to confirm:**
- [ ] EXPLAIN ANALYZE shows the real plan and where time is spent.
- [ ] A sequential scan on a large table is the most common cause of a query that became slow.
- [ ] Outdated statistics are refreshed with ANALYZE.

Notes: 

## ⬜ DB-PERF-002: Index returns wrong results
File: [data/kb/database/DB-PERF-002.md](../../data/kb/database/DB-PERF-002.md) · author A

**Look up:** [SET enable_indexscan = off; SET enable_bitmapscan = off;](https://www.google.com/search?q=PostgreSQL+SET+enable_indexscan+%3D+off%3B+SET+enable_bitmapscan+%3D+off%3B+site%3Apostgresql.org%2Fdocs) · [REINDEX INDEX CONCURRENTLY](https://www.google.com/search?q=PostgreSQL+REINDEX+INDEX+CONCURRENTLY+site%3Apostgresql.org%2Fdocs) · [REINDEX](https://www.google.com/search?q=PostgreSQL+REINDEX+site%3Apostgresql.org%2Fdocs) · [PERF](https://www.google.com/search?q=PostgreSQL+PERF+site%3Apostgresql.org%2Fdocs) · [INDEX](https://www.google.com/search?q=PostgreSQL+INDEX+site%3Apostgresql.org%2Fdocs)

**Key facts to confirm:**
- [ ] Results that change with index scans disabled point to a corrupted index.
- [ ] Corrupted indexes are rebuilt, preferably with REINDEX CONCURRENTLY.
- [ ] Recurring corruption on one volume points to the storage, not the database.

Notes: 

## ⬜ DB-PERF-003: Database server CPU is very high
File: [data/kb/database/DB-PERF-003.md](../../data/kb/database/DB-PERF-003.md) · author A

**Look up:** [pg_stat_activity](https://www.google.com/search?q=PostgreSQL+pg_stat_activity+site%3Apostgresql.org%2Fdocs) · [pg_stat_statements](https://www.google.com/search?q=PostgreSQL+pg_stat_statements+site%3Apostgresql.org%2Fdocs) · [PERF](https://www.google.com/search?q=PostgreSQL+PERF+site%3Apostgresql.org%2Fdocs)

**Key facts to confirm:**
- [ ] pg_stat_statements ranks queries by total execution time.
- [ ] High CPU is usually caused by a few expensive queries.
- [ ] Restarting the database is not a fix for high CPU.

Notes: 

## ⬜ DB-PERF-004: Table keeps growing although rows are deleted
File: [data/kb/database/DB-PERF-004.md](../../data/kb/database/DB-PERF-004.md) · author A

**Look up:** [n_dead_tup](https://www.google.com/search?q=PostgreSQL+n_dead_tup+site%3Apostgresql.org%2Fdocs) · [last_autovacuum](https://www.google.com/search?q=PostgreSQL+last_autovacuum+site%3Apostgresql.org%2Fdocs) · [pg_stat_user_tables](https://www.google.com/search?q=PostgreSQL+pg_stat_user_tables+site%3Apostgresql.org%2Fdocs) · [pg_stat_activity](https://www.google.com/search?q=PostgreSQL+pg_stat_activity+site%3Apostgresql.org%2Fdocs) · [VACUUM (ANALYZE)](https://www.google.com/search?q=PostgreSQL+VACUUM+%28ANALYZE%29+site%3Apostgresql.org%2Fdocs) · [VACUUM FULL](https://www.google.com/search?q=PostgreSQL+VACUUM+FULL+site%3Apostgresql.org%2Fdocs) · [PERF](https://www.google.com/search?q=PostgreSQL+PERF+site%3Apostgresql.org%2Fdocs) · [VACUUM](https://www.google.com/search?q=PostgreSQL+VACUUM+site%3Apostgresql.org%2Fdocs) · [FULL](https://www.google.com/search?q=PostgreSQL+FULL+site%3Apostgresql.org%2Fdocs)

**Key facts to confirm:**
- [ ] Updates and deletes leave dead rows that autovacuum cleans up.
- [ ] Long-running transactions prevent dead rows from being removed.
- [ ] VACUUM FULL takes an exclusive lock on the table.

Notes: 

## ⬜ DB-STO-001: Database disk almost full
File: [data/kb/database/DB-STO-001.md](../../data/kb/database/DB-STO-001.md) · author A

**Look up:** [pg_wal](https://www.google.com/search?q=PostgreSQL+pg_wal+site%3Apostgresql.org%2Fdocs) · [pg_replication_slots](https://www.google.com/search?q=PostgreSQL+pg_replication_slots+site%3Apostgresql.org%2Fdocs)

**Key facts to confirm:**
- [ ] A growing pg_wal directory points to a stuck replication slot or failed WAL archiving.
- [ ] Expanding the volume restores service fast but does not fix the cause.
- [ ] Files in pg_wal are never deleted by hand.

Notes: 

## ⬜ DB-STO-002: Backup before a change or restore after data loss
File: [data/kb/database/DB-STO-002.md](../../data/kb/database/DB-STO-002.md) · author A

**Look up:** [UPDATE](https://www.google.com/search?q=PostgreSQL+UPDATE+site%3Apostgresql.org%2Fdocs) · [DELETE](https://www.google.com/search?q=PostgreSQL+DELETE+site%3Apostgresql.org%2Fdocs) · [WHERE](https://www.google.com/search?q=PostgreSQL+WHERE+site%3Apostgresql.org%2Fdocs)

**Key facts to confirm:**
- [ ] Point-in-time recovery can restore to any moment inside the retention window.
- [ ] Restores go to a new database first, never directly over the live one.
- [ ] The exact time of the bad change sets the restore point.

Notes: 

## ⬜ DB-STO-003: Nightly database backup failed
File: [data/kb/database/DB-STO-003.md](../../data/kb/database/DB-STO-003.md) · author A

**Look up:** (no technical terms; check the steps make sense)

**Key facts to confirm:**
- [ ] The backup job log gives the reason for a failed backup.
- [ ] After fixing the cause, an on-demand backup is run immediately.
- [ ] A backup much smaller than usual should be investigated.

Notes: 

## ⬜ DB-STO-004: WAL archiving failing
File: [data/kb/database/DB-STO-004.md](../../data/kb/database/DB-STO-004.md) · author A

**Look up:** [pg_wal](https://www.google.com/search?q=PostgreSQL+pg_wal+site%3Apostgresql.org%2Fdocs) · [archive_command](https://www.google.com/search?q=PostgreSQL+archive_command+site%3Apostgresql.org%2Fdocs) · [pg_stat_archiver](https://www.google.com/search?q=PostgreSQL+pg_stat_archiver+site%3Apostgresql.org%2Fdocs) · [failed_count](https://www.google.com/search?q=PostgreSQL+failed_count+site%3Apostgresql.org%2Fdocs) · [last_failed_wal](https://www.google.com/search?q=PostgreSQL+last_failed_wal+site%3Apostgresql.org%2Fdocs)

**Key facts to confirm:**
- [ ] WAL files are kept until archive_command succeeds.
- [ ] pg_stat_archiver shows archive failures and the last failed WAL file.
- [ ] Point-in-time recovery is not possible while archiving is failing.

Notes: 

