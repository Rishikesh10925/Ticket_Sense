# Knowledge-base article template and key-facts convention (v1)

Owner: Shivaganesh. Blueprint V2 §11.3 and Appendix C.1. Every article in `data/kb/`
follows this template from Week 2 onwards; the 60 V1 articles are converted in Weeks 2
and 3 as part of authoring (mapping in [data/taxonomy.yaml](../data/taxonomy.yaml)).

## File layout

`data/kb/<department-folder>/<article-id>.md`, for example
`data/kb/networking/NET-VPN-001.md`. The article id is `<DEPT>-<TOPIC>-<NNN>` with the
department and topic codes from the taxonomy.

## Template

```markdown
---
id: NET-VPN-001
department: Networking
topic: net-vpn
title: VPN client not connecting
updated: 2026-03-14
served: true            # false for articles in withheld topics
author: R
reviewer: A             # second member who fact-checked it
---

## Symptom
What the user sees, in their words. Include exact error codes and messages.

## Cause
The usual root causes, most likely first.

## Resolution steps
1. One action per step, imperative mood.
2. Steps that need admin rights say so.

## Warnings
Anything that could cause data loss, an outage or a security exposure if done wrong.

## Key facts
- 3 to 6 short, checkable facts (see below).
```

Sections appear in this order, with these exact headings, so chunking (Blueprint §12.1:
by section, 150 to 300 tokens, title and topic prepended) is mechanical.

## Key-facts convention

Key facts are what the LLM judge checks a draft against (Blueprint §11.6), and what a
human reviewer looks for first. Each fact must be:

1. **Atomic**: one claim. "Error 809 means the VPN port is blocked" — not two facts joined by "and".
2. **Checkable from the article**: it appears in Symptom, Cause or Resolution steps.
3. **Decisive**: a draft that gets it wrong or leaves it out is not acceptable. Do not list trivia.
4. **Specific**: names the error code, transaction, setting, number or policy limit.
   "Restart the client" is not a key fact; "Error 809 means UDP 500/4500 is blocked" is.

Three to six facts per article. If an article needs more, it covers two problems and
should be split.

## Dates and freshness

`updated` dates are drawn from a documented distribution so the freshness signal has
something to measure (Blueprint §11.3): 60 percent within the last 12 months, 30 percent
12 to 30 months old, 10 percent older. The authoring script assigns them; the datasheet
discloses this.

## Authoring and review checklist

- [ ] Front matter complete; `id` matches the file name; `topic` exists in the taxonomy.
- [ ] Every resolution step is something a real support engineer would do.
- [ ] Error codes and transaction names are real and used correctly (look them up).
- [ ] No step is dangerous without a warning.
- [ ] Key facts follow the four rules above.
- [ ] LLM-drafted text has been read line by line and edited by the author.
- [ ] A second member reviewed it and is named in `reviewer`.

## Worked example (V1 article converted)

```markdown
---
id: NET-VPN-001
department: Networking
topic: net-vpn
title: VPN client not connecting
updated: 2026-05-02
served: true
author: R
reviewer: S
---

## Symptom
The VPN client hangs at "Connecting...", or fails at once with an authentication or
timeout error.

## Cause
No internet connection; a locked domain account; a network (hotel or public Wi-Fi) that
blocks the VPN port; or a VPN adapter disabled by a Windows update.

## Resolution steps
1. Confirm the internet works without the VPN by loading any public website.
2. Restart the VPN client and retry.
3. If authentication fails, check whether the domain account is locked by signing in to a
   company laptop with the normal domain password.
4. If the client hangs at "Connecting" with no login prompt, retry from a mobile hotspot to
   rule out a network that blocks the VPN port.
5. If the VPN adapter shows as disabled after a Windows update, restart the machine.

## Warnings
Do not ask the user to disable their firewall to test the connection.

## Key facts
- A hang at "Connecting" with no login prompt points to a network blocking the VPN port.
- An authentication failure should be checked against a locked domain account first.
- A mobile hotspot isolates a blocking network from a client fault.
- A VPN adapter disabled after a Windows update is fixed by a restart.
```
