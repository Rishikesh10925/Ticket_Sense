---
id: SAP-ACC-003
department: SAP
topic: sap-access
title: Forgotten SAP password
updated: '2026-02-03'
served: true
author: S
reviewer: null
---

## Symptom
The user has forgotten their SAP password but the account is not locked yet, or they
are asked for a password they never set (first logon to a new system).

## Cause
SAP passwords are separate from the Windows domain password on systems without single
sign-on. Users who rarely log on to a system (for example the quality system) forget them.

## Resolution steps
1. Check whether the system offers single sign-on. If it does, the user should log on
   from SAP Logon without a password while on the company network or VPN.
2. If not, ask the user to use the self-service password reset in the SAP portal with
   their employee ID. This works only if their profile has a verified mobile number.
3. If self-service is not possible, verify their identity as for an unlock request and
   set a new initial password in SU01 (Change Password).
4. Remind the user that each SAP system (development, quality, production) has its own
   password.

## Warnings
Do not set a productive password for the user. Always use an initial password so the
user has to choose their own.

## Key facts
- Each SAP system has its own password unless single sign-on is used.
- Self-service reset needs a verified mobile number in the user's profile.
- The helpdesk fallback is an initial password set in SU01 after identity verification.
