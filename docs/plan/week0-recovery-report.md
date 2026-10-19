# Week 0 Recovery Report (16 to 18 October 2026)

Companion to [TicketSense_Master_Blueprint.docx](TicketSense_Master_Blueprint.docx) and
[TicketSense_Master_Roadmap.docx](TicketSense_Master_Roadmap.docx) (Version 2.0).

## What exists (inventory)

| Area | What is there |
|---|---|
| Backend | FastAPI app, JWT auth, three roles, ticket lifecycle, escalations, feedback, analytics, messaging. Alembic migrations 0001 to 0010. |
| Pipeline | LangGraph graph: extract, classify, retrieve, score, gate, draft. Drafting uses a deterministic stub (no real LLM). |
| Retrieval | Dense MiniLM embeddings in pgvector, department filter in the SQL. No keyword search, no fusion, no reranker. |
| Models | TF-IDF + logistic regression classifiers (department, priority, sentiment). Logistic-regression confidence model trained on formula-generated synthetic labels. |
| Data | Public multilingual ticket set (2 of 5 departments represented), 120 synthetic tickets, 60 KB articles without front matter. |
| Frontend | React + TypeScript + Vite, three role areas, admin dashboard, threshold screen, dark mode, chat. |
| Ops | Render/Vercel deployment, keep-warm cron. No CI that runs tests. |
| Docs | Weekly integration notes, model and metric docs (honest about limits). |

## What went wrong (no blame)

1. Effort drifted to UI polish and deployment while the research core (benchmark, labels,
   baselines, evaluation) never started.
2. Confidence labels were simulated from a formula, so the confidence model learned the
   formula back (ROC-AUC 0.57 on real rows). This is the circular-label problem.
3. The public dataset covers Networking almost exclusively, so the classifier's macro-F1
   is 0.45 and Database scores 0.0.
4. No real LLM was ever wired in, so "groundedness" was measured on extracted text.
5. A customer auto-resolution path (score >= 0.85, no human) crept in, which contradicts
   the core promise that a human always makes the final decision.
6. Evaluation was left for the end; there is no harness, no locked test, no baseline.

## Audit decisions

| Component | Decision | Reason | Owner |
|---|---|---|---|
| Auth, roles, RBAC | Keep | Matches Blueprint §8 core item 1 | R |
| Ticket API, lifecycle, queues | Keep | Matches core item 2 | R |
| Schema and migrations | Keep, extend | Add V2 tables incrementally (kb_chunks, drafts, claims, signals, gate_decisions, labels, experiments) | R |
| Department-scoped SQL retrieval | Keep, extend | Add full-text search, RRF and a cross-encoder in Week 4 | R |
| LangGraph pipeline | Rewrite order | V2 needs draft and claim check *before* scoring | R |
| LLM provider interface | Keep interface, add real provider + cache | Week 1 | R |
| Customer auto-resolution | **Drop now** | Violates "a human always decides" (Blueprint §7, §9.1) | R |
| Stub drafter | Keep only as a test double | Real drafts come from the local LLM | R |
| Classifier (TF-IDF LR) | Rewrite in Week 3/4 | Retrain on the V2 benchmark; add uncertainty output | S |
| Confidence model + synthetic labels | Drop | Circular labels; replaced by the V2 confidence engine | S |
| Public dataset | Replace as primary source | Fully synthetic benchmark; public set kept only as a style seed (ADR 003) | S |
| KB articles (60) | Keep after review | Convert to the template with front matter and key facts; extend to 120 | All |
| Frontend shell and components | Keep | Matches the three-role design | A |
| Engineer review UI | Rewrite to three-lane workbench | Week 7 to 9 | A |
| Admin dashboard, threshold screen | Keep | Extended tier, already built; no further polish | A |
| OCR (images) | Park behind a flag | Stretch item; cut list item 1 | R |
| Messaging, chat widget | Freeze | Out of scope; no further work | A |
| Render/Vercel deployment | Freeze | Out of scope (Blueprint §8); keep it running, no further work | R |
| Docs | Reuse text | Rewrite where they claim V1 behaviour | All |

## Decisions for Week 1

- LLM provider: local open-weight model on the team GPU via Ollama (ADR 002).
- Benchmark: fully synthetic with provenance; public data as style seed only (ADR 003).
- Workflow: per-member weekly branches merged directly into `main`; no pull requests.
  CI must stay green on `main` instead of being enforced by branch protection.
