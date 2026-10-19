# Network Port Not Working at New Desk

**Department:** Networking

## Issue
A wired network port at a new or reassigned desk shows no link light /
"network cable unplugged" even though the cable is connected.

## Resolution
1. Confirm the cable itself is good by testing it (or a known-good cable) at
   a working port elsewhere.
2. Check the patch panel labeling for that desk against the switch port it's
   actually patched to — desk moves often leave stale patch documentation.
3. If the physical patch is correct, the switch port may not be configured
   with the right VLAN for that desk's location/department — this requires
   a switch config change, not a physical fix.
4. New desks in a freshly built-out area may simply not have their port
   activated yet — check the office buildout ticket before assuming a fault.

## Notes
Always confirm patch panel labeling physically rather than trusting
documentation alone — it drifts out of date after office moves.
