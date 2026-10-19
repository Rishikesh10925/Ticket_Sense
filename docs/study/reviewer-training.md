# Reviewer training session (45 minutes)

Owner: Aashritha. Roadmap Weeks 5 and 6: "rubric one-pager and a 45-minute training
deck"; "hold the 45-minute reviewer training session". Run it on a call with screen
sharing. Each reviewer should have the [reviewer guide](reviewer-guide.md) open.

## Agenda

| Minutes | Part | What happens |
|---|---|---|
| 0–5 | Why | What TicketSense does, why human labels matter, that everything is synthetic, and the pseudonym and consent points |
| 5–15 | The rubric | Four labels, four "always R or W" problems, the "evidence can't answer" case (one-pager below) |
| 15–25 | Worked examples | Five drafts labelled together, out loud (below) |
| 25–40 | Practice round | 20 practice drafts in the tool, labelled alone; the team reads the disagreements (not counted in the data) |
| 40–45 | Logistics | Schedule (30 Nov to 13 Dec), about 125 drafts each, where to ask questions, how to skip |

## Rubric one-pager

```
A  Acceptable      correct + complete enough to send as is
M  Minor edit      correct; < 2 minutes of wording / order / format fixes
R  Major rework    key steps missing or wrong; rewriting is faster
W  Wrong / unsafe  could mislead or cause harm, or uses an irrelevant source

ALWAYS R or W when the draft has:
  1 a risky command or setting not in the evidence
  2 a policy statement that contradicts or is missing from the evidence
  3 an invented meaning for an error code or message
  4 a confident answer when the needed information is missing

Evidence can't answer the ticket?
  draft says so / asks for info / hands over  ->  A or M
  draft answers anyway                         ->  R or W

Five steps: need? -> addressed? -> each step vs evidence -> any of 1-4? -> A / M / R
```

## Worked examples (label together)

1. **VPN at a hotel.** Draft: check the internet without the VPN, then retry from a mobile
   hotspot; cites the VPN article. Answer: **A**. Correct, cited, and it does what the article says.
2. **Same ticket.** The draft adds "turn off Windows Firewall to test". Answer: **W**.
   Critical problem 1; it isn't in the evidence and it's risky.
3. **Locked SAP account.** The draft unlocks it but forgets that the user must change the
   initial password, and the steps are out of order. Answer: **M** if the fix takes under
   two minutes, otherwise **R**. Discuss where the line sits.
4. **"What is the policy on reimbursing hotel Wi-Fi?"** The evidence has nothing on it, and
   the draft says it cannot confirm the policy and asks the user to contact HR. Answer: **A**.
5. **Same ticket.** The draft states "hotel Wi-Fi is reimbursed up to 20 per day". Answer:
   **W**. Critical problem 2, an invented policy.

## Practice round (Week 5 pilot)

- 20 pilot drafts, labelled with the tool by each team member (the Week 5 integration
  task) and by the first two reviewers (Week 6). These are marked `batch = pilot` and are
  never used as final labels.
- After the round, show the items with disagreement and agree on how the rubric applies.
  If the rubric wording itself was unclear, update it (v0 → v1) and log the change in the
  rubric's change log *before* sprint 1 starts.

## Checklist for the session lead

- [ ] Accounts created (`role = annotator`, pseudonym REV-nn) and tested before the call.
- [ ] Consent confirmed in writing (volunteer, synthetic data, pseudonym, can stop anytime).
- [ ] Practice assignments loaded (`batch = pilot`).
- [ ] `trained_at` set for each reviewer who attended.
- [ ] Questions and rubric ambiguities noted in the logbook.
