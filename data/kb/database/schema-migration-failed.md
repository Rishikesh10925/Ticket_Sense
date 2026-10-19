# A Failed Schema Migration and How to Recover

**Department:** Database

## Issue
A schema migration (e.g. an Alembic migration) fails partway through, leaving
the database in an uncertain state — some DDL may have applied, some may not
have.

## Resolution
1. Check the migration tool's version table (e.g. `alembic_version`) to see
   whether it recorded the migration as applied or not — this tells you
   whether the tool believes it succeeded, which may not match reality if it
   failed after the DDL but before recording the version.
2. Inspect the actual schema against what the migration was supposed to
   produce, rather than trusting the version table alone, to find exactly
   which statements did and didn't apply.
3. If the migration wasn't wrapped in a transaction (some DDL can't be, e.g.
   `CREATE INDEX CONCURRENTLY`), manually complete or roll back the partial
   change to match one consistent state before retrying.
4. Once the schema and version table agree on a consistent state, re-run the
   migration (if rolled back) or mark it applied (if manually completed) —
   never retry blindly without confirming the starting state first.

## Notes
Migrations that mix transactional DDL with non-transactional statements (like
`CREATE INDEX CONCURRENTLY`) are the most common source of a genuinely
ambiguous partial-failure state — split those into separate migrations where
possible to avoid this class of problem entirely.
