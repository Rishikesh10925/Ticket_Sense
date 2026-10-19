---
id: CLD-VM-001
department: Cloud
topic: cloud-compute
title: Cannot SSH into a cloud virtual machine
updated: '2026-08-03'
served: true
author: A
reviewer: null
legacy: ec2-ssh-unreachable
---

## Symptom
SSH to a cloud virtual machine times out or is refused, either for a machine that worked
before or for one that was just launched.

## Cause
A timeout usually means the network blocks the connection: the security group does not
allow port 22 from the user's address, or the machine is in a private subnet. A refusal or
authentication failure means the network is fine but the key or SSH configuration is wrong.

## Resolution steps
1. Check that the instance is running and that both status checks pass. A failed system
   status check is a host problem: stop and start the instance.
2. If the connection times out, check that the security group allows inbound port 22 from
   the user's current IP address.
3. For machines in a private subnet, connect through the bastion host or the VPN; direct
   SSH from the internet is not expected to work.
4. If the connection is refused or authentication fails, confirm the user is using the
   key pair the instance was launched with and the right user name for the image.

## Warnings
Never open port 22 to 0.0.0.0/0 (the whole internet) to fix access.

## Key facts
- An SSH timeout points to a network block such as a security group rule.
- A refused connection or failed authentication points to the key or SSH configuration.
- Private-subnet machines are reached through the bastion host or VPN.
- A failed system status check is fixed by stopping and starting the instance.
