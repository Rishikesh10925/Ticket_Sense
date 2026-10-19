# EC2 Instance Unreachable via SSH

**Department:** Cloud

## Issue
Cannot SSH into an EC2 instance that was previously reachable, or a newly
launched instance never accepts a connection.

## Resolution
1. Check the instance state (running vs. stopped) and status checks in the
   console — a failed system status check points to a host-level issue, not
   something fixable from inside the instance.
2. Verify the security group attached to the instance allows inbound SSH
   (port 22) from the connecting IP — this is the most common cause for a
   newly launched instance.
3. Confirm the correct key pair is being used — a mismatched key produces a
   connection that's accepted at the TCP level but rejected during
   authentication, which looks different from a security-group block (which
   times out entirely).
4. For instances in a private subnet, confirm access is via a bastion host
   or VPN, not a direct public IP — direct SSH from the internet isn't
   expected to work by design there.

## Notes
A connection that times out (no response) usually means a security
group/network ACL block; a connection that's refused or drops during auth
usually means a key or SSH config issue on the instance itself.
