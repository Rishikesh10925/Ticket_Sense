# ADR 003: Benchmark data source — fully synthetic with provenance

- Status: accepted
- Date: 2026-10-19
- Owner: Shivaganesh
- Roadmap Week 1 exit gate: "Dataset decision made (public or fully synthetic)"

## Context

Blueprint §11.2 asks for a public ticket dataset as a style seed and extra classifier
data, "if a suitable set exists". V1 used Tobias Bueck's *Customer IT Support Ticket
Dataset* (Kaggle / Hugging Face, CC-BY-NC-4.0; see [dataset-research.md](../dataset-research.md)).

Shortlist checked in Week 1:

| Dataset | Licence | Resolution text | Fit to our 5 departments |
|---|---|---|---|
| Bueck, Customer IT Support Tickets (28.6k, EN/DE) | CC-BY-NC-4.0 | Yes (`answer`) | Poor: after V1 mapping, 7,343 of 7,691 English rows are Networking, 348 HR, and **zero** SAP, Cloud or Database |
| Bitext customer-support intents | CDLA-Sharing | Template answers | Retail/e-commerce intents, not IT |
| ServiceNow/Jira public exports | Mixed, mostly unclear | Rarely | Licences unclear; not redistributable |

None of them carries what the trust gate needs most: **provenance** (which KB article
answers the ticket) and **deliberately unanswerable tickets**.

## Decision

1. The benchmark is **fully synthetic with provenance** (Blueprint §11.4). Tickets are
   generated from specific KB articles with controlled difficulty, so every ticket is
   typed A / B / C1 / C2 by construction.
2. The Bueck dataset is used **only as a style reference**: its length distribution,
   typo rate and phrasing patterns set the generator's noise settings. It is not used to
   train the V2 classifier (its labels cover two of five departments, which is why V1's
   macro-F1 is 0.45) and it is never redistributed.
3. The released benchmark and datasheet state plainly that tickets and articles are
   synthetic or synthetic-assisted, and never claim they are real company data.

## Consequences

- The V2 classifier trains on the benchmark's train split, which is balanced across five
  departments by construction.
- Risk R4 (synthetic benchmark too easy) becomes the main threat to validity. Mitigations
  are in the generator: typos, vague wording, multi-issue tickets, pasted logs, unseen
  topics, and the 15 percent partly-answerable type B.
- The CC-BY-NC licence no longer matters for the release, since nothing from that dataset ships.
