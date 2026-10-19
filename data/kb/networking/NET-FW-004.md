---
id: NET-FW-004
department: Networking
topic: net-firewall
title: Application cannot send email from the office network
updated: '2026-05-26'
served: true
author: R
reviewer: null
---

## Symptom
A script, scanner or application that sends email directly fails to connect to the mail
server on port 25, while the same email account works in Outlook.

## Cause
Outbound SMTP on port 25 is blocked for all devices except the company mail relay, to
stop infected machines from sending spam.

## Resolution steps
1. Confirm what is sending the email: a device (scanner, printer) or an application.
2. Configure it to send through the internal mail relay, whose address is on the
   intranet, instead of an outside mail server.
3. If the relay needs to accept a new device, raise a request with the device's IP and
   the sender address it will use.

## Warnings
Do not request a firewall exception for port 25 to the internet.

## Key facts
- Outbound port 25 is blocked except from the company mail relay.
- Devices and applications must send email through the internal mail relay.
- A new device needs its IP registered with the relay.
