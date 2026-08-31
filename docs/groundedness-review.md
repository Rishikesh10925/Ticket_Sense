# Groundedness review

Week 6 note (Shivaganesh) — the manual review of generated drafts the roadmap's Mentor
Review calls for ("logbook entry: groundedness review notes"). Read
[docs/draft-generation.md](draft-generation.md) first — this review is of the current
**extractive stub provider**, not a generative LLM, which materially changes what a
"grounded" result here demonstrates.

## Sample

10 tickets, 2 per department, phrased the way an End User would actually write them
(not copied from KB titles) — the same set used for
[docs/team-integration-week5.md](team-integration-week5.md)'s leakage check, reused
here for continuity between weeks. For each: retrieved top-3 evidence, built the
prompt, generated a draft with `StubLLMProvider`, ran `check_groundedness`.

## Results

**10/10 drafts fully grounded** — 30/30 citations valid (mapped to a real evidence
item), 0 uncited substantive lines.

| Department | Ticket | Evidence used | Groundedness |
|---|---|---|---|
| SAP | ME023 error on goods receipt | 2 resolved tickets + ME023 KB article | ✅ 3/3 |
| SAP | SAP account locked | 2 resolved tickets + account-lock KB article | ✅ 3/3 |
| Networking | VPN not connecting | 2 resolved tickets + VPN KB article | ✅ 3/3 |
| Networking | Office wifi dropping | 2 resolved tickets + wifi KB article | ✅ 3/3 |
| Cloud | S3 access denied | 2 resolved tickets + S3 KB article | ✅ 3/3 |
| Cloud | EC2 unreachable | 2 resolved tickets + EC2 KB article | ✅ 3/3 |
| Database | Connection pool exhausted | 2 resolved tickets + pool KB article | ✅ 3/3 |
| Database | Deadlock error | 2 resolved tickets + deadlock KB article | ✅ 3/3 |
| HR | Leave request process | 2 resolved tickets + leave KB article | ✅ 3/3 |
| HR | Missing payslip | 2 resolved tickets + payroll KB article | ✅ 3/3 |

## Manual read of citation correctness (not just marker validity)

`check_groundedness` only verifies a citation marker points to a real evidence item —
it doesn't check that the *content* next to the marker actually matches that item. So
each draft was also read by hand to confirm the cited text is genuinely what the
evidence says, not just correctly numbered. Two examples, representative of the rest:

**SAP / ME023 error** — evidence item [3] is the KB article's own `## Resolution`
section, and the draft's [3] line is that section's first two steps verbatim
("Open the PO in ME23N and check the Delivery and Invoice tabs..."). Correct.

**HR / Leave request process** — evidence item [2] is the leave-policy KB article's
resolution steps; the draft's [2] line quotes them directly ("Submit the leave request
through the HR portal..."). Correct.

Since the provider is extractive, this manual check is closer to "does the extraction
logic pick sensible spans and not scramble them" than "does the model reason correctly
about the evidence" — worth being explicit about, per
[draft-generation.md](draft-generation.md).

## Quality issues found, not caught by the groundedness checker

The checker measures citation validity, not draft *quality* — two real issues found by
reading the output, neither of which is a groundedness failure:

1. **Resolved-ticket evidence sometimes restates the question, not an answer.** For
   several tickets (e.g. SAP account locked, item [1] and [3]), the cited "evidence"
   is another user's *complaint* ("I can't log into SAP GUI anymore...") rather than a
   resolution — because the synthetic resolved-ticket set (Week 4/5) doesn't include a
   distinct resolution field per ticket, retrieval surfaces similar problem
   descriptions, not solutions, for that source type. The KB-article citation in each
   draft does carry the actual fix; the resolved-ticket citations mostly corroborate
   "yes, this is a known issue" rather than adding new resolution steps. Worth revisiting
   once real resolved tickets (with an actual final response) exist.
2. **Truncated resolution text originally ended mid-sentence** ("...ask the
   requesting department..." with no continuation) — the 220-character truncation in
   `_key_snippet` (`ai/generation/llm_interface.py`) cut at a word boundary, not a
   sentence boundary. Fixed during this review: it now prefers cutting at the end of a
   sentence within the character window. Re-running the same 10 tickets afterward,
   every draft ends on a complete sentence — though for a numbered-step resolution,
   that sometimes means ending right after a bare "2." with the step's content cut off,
   since "N. " is treated as a sentence boundary too. Improved, not perfect; a real
   generative provider wouldn't have this specific failure mode at all.

## Honest bottom line

The groundedness *mechanism* — checking that every citation maps to real evidence, and
that cited text actually reflects that evidence — works and was verified to actually
catch problems (see [draft-generation.md](draft-generation.md)'s checker self-test).
What it does **not** demonstrate is that TicketSense can produce grounded output from a
real generative LLM under realistic hallucination pressure, since none was available to
test against. That remains open for whenever a real provider is added.
