# 11. User experience and the user study

*Owner: Aashritha. Draft (Week 12). Results: **To be filled** after the sessions.*

## 11.1 Designing for the decision, not the draft

The engineer's question on every ticket is "can I send this, and what must I check?". The
workbench answers it per lane:

| Lane | What the engineer sees | Intended behaviour |
|---|---|---|
| Fast | The draft, ready to send, with citations | Read once, accept or edit |
| Assisted | The draft, the reasons it was not fast, and "Weakest claims: verify these first" (the three lowest-support claims) next to the evidence | Check the flagged claims, then accept, edit or escalate |
| Escalate | No AI draft; the reasons and the evidence | Answer from the knowledge base, or escalate further |

Design choices:

- **No draft below the gate.** An escalated ticket never shows a draft, because a weak
  draft that is visible anchors the engineer (Blueprint V2 §9.1).
- **Reasons in words, not numbers.** The gate's top reasons ("low reranker score",
  "another department matches as well") are shown instead of the raw score.
- **The queue shows the lane** as a badge and can be filtered by lane, so engineers can
  batch quick tickets.
- **End users never see** drafts, scores or evidence; they see the final reply.

## 11.2 Accessibility

A Week 10 pass with the JSX accessibility rules fixed six problems (mouse-only contacts,
approval items and links; unlabelled table headers). The Week 11 bug bash found that ticket
rows in all three roles opened only on a mouse click; ticket subjects are now links, and
opening a ticket with Tab and Enter was checked for every role. Details:
[usability-pass-week10.md](../study/usability-pass-week10.md),
[bug-bash-week11.md](../bug-bash-week11.md). The manual keyboard, screen-reader and zoom
walk-through is **To be done** by a person.

## 11.3 The user study (H4)

Pre-registered hypothesis H4: the workbench cuts median handling time by at least 20% with
no increase in accepted major errors, reported descriptively with a small-sample caveat.

| Item | Design |
|---|---|
| Participants | 6 to 8, acting as engineers, not project authors |
| Conditions | Manual (ticket and knowledge-base search) versus workbench (lanes, drafts, reasons, weakest claims) |
| Tickets | Two matched sets of 20: per set 11 A, 3 B, 4 C1, 2 C2, four per department; never from the locked test or the labelling selection |
| Order | Within subject; set A always first; condition order alternates by sign-up |
| Stimuli | Every participant sees the same draft and lane for a ticket (fixed when accounts are created) |
| Measures | Handling time per ticket, measured on the server; final replies graded blind with the rubric; SUS after the workbench condition |
| Ethics | Synthetic tickets only; consent form; participants recorded as P01, P02, … |

The study tool was tested end to end in a browser with a throwaway participant (Week 11).
With the current thresholds there is no fast lane; set A has 12 assisted and 8 escalated
tickets, set B 14 and 6. This imbalance is reported with the results.

## 11.4 Results

**To be filled**: median handling time per condition and the paired reduction with its
interval; accepted major errors per condition; SUS mean; what participants said helped and
got in the way (`python ai/study/analyse.py`).
