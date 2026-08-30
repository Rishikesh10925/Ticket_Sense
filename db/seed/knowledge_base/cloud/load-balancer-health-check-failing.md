# Load Balancer Health Check Failing

**Department:** Cloud

## Issue
Load balancer marks one or more backend instances/targets as unhealthy,
reducing available capacity or causing intermittent request failures.

## Resolution
1. Check the configured health check path and expected response code —
   confirm the application is actually serving that exact path correctly.
2. Manually hit the health check endpoint directly on the affected
   instance (bypassing the load balancer) to see if it responds as
   expected.
3. If the endpoint responds fine directly but the load balancer still marks
   it unhealthy, check the health check timeout/threshold settings and
   security group rules between the load balancer and the target.
4. If the application itself is failing the check (slow startup, dependency
   not ready), this is an application issue to route to the owning team, not
   a load balancer configuration problem.

## Notes
A target flapping between healthy/unhealthy usually points to a
resource-contention issue (CPU/memory) on the instance rather than a load
balancer config problem.
