---
id: DB-CONN-004
department: Database
topic: db-connectivity
title: Connection rejected with no pg_hba.conf entry
updated: '2025-07-22'
served: true
author: A
reviewer: null
---

## Symptom
A new application server or a developer gets "no pg_hba.conf entry for host" when
connecting to a PostgreSQL database.

## Cause
PostgreSQL only accepts connections that match a rule in `pg_hba.conf`, which lists the
allowed host addresses, databases, users and whether SSL is required. A new host, or a
client without SSL where SSL is required, matches no rule.

## Resolution steps
1. Read the full error: it names the client address, user, database and whether SSL was used.
2. If the client connected without SSL, set the client to require SSL and retry.
3. If the host is new, raise a change request to add it, with the address, user, database
   and business reason.
4. The DBA team adds the rule and reloads the configuration.

## Warnings
Never request a rule that allows all addresses or "trust" authentication.

## Key facts
- "no pg_hba.conf entry" means no rule allows that host, user, database and SSL setting.
- The error message names the client address, user and database.
- pg_hba.conf changes are made by the DBA team through a change request.
