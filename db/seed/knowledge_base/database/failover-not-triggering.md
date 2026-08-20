# Automated Failover Not Triggering as Expected

**Department:** Database

## Issue
The primary database becomes unavailable (crash, network partition) but the
configured automated failover to a standby doesn't happen, or takes far
longer than expected.

## Resolution
1. Check the failover mechanism's own health checks — a common cause is the
   health check itself still reporting the primary as "up" (e.g. it checks
   the port is open but not that queries actually succeed), so failover never
   triggers.
2. Check whether the failure was a full outage or a partial/intermittent one
   — many failover systems intentionally wait through brief blips to avoid
   flapping, which looks identical to "not triggering" for the first
   30–60 seconds.
3. Check quorum/consensus requirements if the setup uses one (e.g. requiring
   a majority of nodes to agree the primary is down) — a failure that also
   takes out part of the quorum can prevent failover from being safely
   decided at all.
4. If failover genuinely didn't fire when it should have, promote the standby
   manually to restore service first, then investigate the failover
   configuration afterward — don't let root-causing block recovery.

## Notes
A failover system that never gets exercised outside real incidents is a risk
in itself — this incident is also a signal to schedule a deliberate failover
drill once things are stable again.
