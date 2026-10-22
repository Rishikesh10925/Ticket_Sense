# 1. Introduction

*Owner: Aashritha. Draft v1.*

## 1.1 Problem

IT and HR helpdesks receive many tickets that a knowledge-base article already answers.
A language model can draft those answers, but a draft is only useful if the engineer can
tell when to trust it. A wrong draft that looks confident costs more than no draft: the
engineer either checks everything (no time saved) or misses the error (harm done).

TicketSense treats this as a decision problem: **for each ticket, should an AI draft be
shown at all, and how much checking does it need?** A confidence model, trained separately
from the language model, scores every draft. Statistically certified thresholds then send
it to one of three lanes:

- **fast**: confident enough to send after a quick read;
- **assisted**: shown, with its weakest claims flagged for checking;
- **escalate**: no AI draft; a human handles the ticket.

## 1.2 Research questions

From the [pre-registration](../prereg.md):

| ID | Question |
|---|---|
| RQ1 | Does an independently trained confidence model rank drafts by correctness better than the strongest single signals? |
| RQ2 | Can statistical threshold selection hold the fast-lane error rate under a chosen budget on unseen tickets? |
| RQ3 | How do retrieval and grounding quality limit draft quality, and how does the gate behave on unanswerable tickets and unseen topics? |
| RQ4 | Does the lane design reduce handling time without increasing accepted errors? |

## 1.3 Contributions

1. A working three-role helpdesk (end user, department engineer, admin) whose LangGraph
   pipeline redacts, classifies, routes, retrieves, drafts with citations, checks claims
   and gates every ticket (Chapter 3).
2. A benchmark of 1,775 synthetic tickets with known provenance, including tickets the
   knowledge base cannot answer, frozen and hashed before labelling (Chapter 4).
3. A confidence model over 31 signals plus category history, with Platt calibration and
   Learn-then-Test thresholds, compared against seven baselines (Chapters 6 and 7).
4. A shift guard for topics the knowledge base does not cover, tuned and evaluated on
   disjoint topics (Chapter 7).
5. An injection red team run through the full pipeline (Chapter 8) and one-command,
   fresh-clone reproduction of every development table (Appendix).

## 1.4 Status of the results

Every number in this draft is a development number on the validation split with labels
from an LLM judge. The pre-registered results need human labels and one run on the
sealed locked test: **To be filled** (Chapter 7).
