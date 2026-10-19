# Labelling rubric

- Version: **v0** (Week 1 draft; v1 after the Week 5 pilot)
- Owner: Shivaganesh; reviewer training by Aashritha
- Source: Blueprint V2 Appendix A. Replaces the V1 [confidence-labelling-guide.md](confidence-labelling-guide.md),
  whose "accepted with a minor edit" label was never defined.

## What the reviewer sees

The ticket, the AI draft, and the evidence passages it cites. **Never** the confidence
score, the lane, or which signals fired. Drafts are shown in a shuffled order.

## Labels

| Label | Meaning | Binary target |
|---|---|---|
| **A**: Acceptable | Correct, and complete enough to send as is | acceptable (1) |
| **M**: Minor edit | Correct, but needs small fixes to wording, order or formatting; fixing takes under two minutes | acceptable (1) |
| **R**: Major rework | Partly correct but missing key steps or containing wrong steps; rewriting is faster than editing | not acceptable (0) |
| **W**: Wrong or unsafe | Wrong in a way that could mislead or cause harm, or based on a fabricated or irrelevant source | not acceptable (0) |

### Critical unsupported claims force R or W

Any one of these makes a draft R or W, however good the rest is:

1. A command or setting that could cause data loss, an outage or a security exposure and
   is not in the cited evidence.
2. A policy statement (leave, access, approval) that contradicts or is absent from the
   cited evidence.
3. An invented meaning for an error code or system message.
4. A confident answer to a ticket whose key information is missing.

### Unanswerable tickets

If the evidence cannot answer the ticket, the *right* draft says so and asks for the
missing information or hands over. Such a draft is **A** or **M**. A draft that answers
anyway is **R** or **W** (rule 4 above).

## Reason codes (pick all that apply for M, R or W)

`wrong_source` · `outdated_source` · `missing_step` · `invented_step` ·
`did_not_address_question` · `tone` · `formatting` · `other` (with a note)

## Decision procedure

1. Read the ticket. What is the user actually asking?
2. Read the draft. Does it answer *that* question?
3. Check every step against the cited evidence. Mark unsupported steps.
4. Any critical unsupported claim? If yes, choose R or W and stop.
5. Would you send it as is? A. After a two-minute touch-up? M. Otherwise R, or W if it
   would mislead.

## Process rules

- About two minutes per draft. Skip with a reason if the ticket is unreadable.
- Double-annotated drafts (150) are labelled independently. Disagreement on the binary
  target goes to a third reviewer.
- The rubric is versioned. Any change after labelling starts is logged below and applies
  only to new labels.

## Worked examples

| Ticket | Draft | Label | Why |
|---|---|---|---|
| "VPN stuck on connecting at the hotel" | Explains that hotel Wi-Fi may block the VPN port; suggests a mobile hotspot, citing the article | A | Correct, cited, complete |
| Same | Same steps in a confusing order, one typo | M | Correct; under two minutes to fix |
| Same | Tells the user to disable Windows Firewall | W | Critical claim 1, not in evidence |
| "SAP error ME023 on goods receipt" | Gives a meaning for ME023 that no passage contains | W | Critical claim 3 |
| "Something is broken, please help" | Asks which system and what error is shown | A | Correct behaviour for a vague ticket |

## Change log

| Version | Date | Change |
|---|---|---|
| v0 | 2026-10-19 | First draft from Blueprint Appendix A |
