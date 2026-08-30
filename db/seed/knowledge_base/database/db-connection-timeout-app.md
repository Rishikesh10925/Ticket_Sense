# Application-Side Connection Timeouts to the Database

**Department:** Database

## Issue
An application intermittently times out trying to connect to the database,
while direct connections from a database client (e.g. `psql`) succeed
without issue.

## Resolution
1. Confirm the database server itself isn't at its connection limit at the
   time of the timeouts (see "Application Errors From an Exhausted
   Connection Pool") — a full server rejects new connections in a way that
   can surface as a client-side timeout.
2. Check network path specifically between the application host and the
   database — a working `psql` connection from a different host doesn't rule
   out a network issue specific to the application's host/subnet/security
   group.
3. Check the application's configured connect timeout — a value that's too
   short for normal (if slightly slow) connection setup will produce
   intermittent timeouts under mild load that aren't a real outage.
4. If timeouts cluster around a specific time of day, check for a scheduled
   job (backup, batch import) that saturates the database's connection slots
   or network bandwidth during that window.

## Notes
"Works from psql but not from the app" almost always means the difference is
environmental (network path, connection pool exhaustion, timeout config) —
it's rarely a database configuration issue at that point.
