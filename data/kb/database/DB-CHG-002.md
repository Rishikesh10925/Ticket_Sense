---
id: DB-CHG-002
department: Database
topic: db-change
title: Schema migration failed halfway
updated: '2025-12-09'
served: true
author: A
reviewer: null
legacy: schema-migration-failed
---

## Symptom
A schema migration failed during deployment, and it is unclear which changes were applied.

## Cause
Migrations that are not run in one transaction (for example with `CREATE INDEX
CONCURRENTLY`) can stop halfway. The migration tool's version table may not match what
was really applied.

## Resolution steps
1. Check the version table (for example `alembic_version`) to see what the tool recorded.
2. Compare the actual schema with what the migration should produce.
3. Finish or undo the partial change by hand so the schema matches one known version.
4. Then mark the version or rerun the migration, and record what was done in the ticket.

## Warnings
Never rerun a failed migration before you know which statements already applied.

## Key facts
- The migration version table may not match the real schema after a failure.
- Non-transactional statements like CREATE INDEX CONCURRENTLY can leave partial changes.
- The schema is brought to one consistent version before rerunning.
