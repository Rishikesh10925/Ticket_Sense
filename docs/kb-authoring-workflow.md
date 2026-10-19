# KB authoring workflow (LLM-assisted, human fact-checked)

Owner: Shivaganesh. Blueprint V2 §11.2 to §11.3: articles are "drafted with LLM help,
then fact-checked and edited by a human author", and every article is reviewed by a
second member. Template: [kb-article-template.md](kb-article-template.md).

## Steps

1. **Pick the slot.** The topic and article id come from [data/taxonomy.yaml](../data/taxonomy.yaml).
   Withheld topics get `served: false`.
2. **Draft.** Write the article in the template, with LLM help if you like. Convert a V1
   article by keeping its facts, adding Cause, Warnings and Key facts, and setting
   `legacy: <old-file-slug>`.
3. **Author edit.** Read every line. Remove anything you would not tell a colleague. Every
   transaction code, parameter, port, menu path and policy number must be one you have
   checked (see the checklist below).
4. **Validate.** Run `uv run --project backend python ai/benchmark/kb.py`. It must say
   "all V2 articles valid".
5. **Second-member review.** Another member reads the article against the checklist and
   puts their initial in `reviewer:`. Until then `reviewer: null`, and the article does
   not count as reviewed. The Week 3 benchmark freeze needs all 120 reviewed.
6. **Ingest.** Run `python ai/embeddings/embed_knowledge_base.py --prune-stale` after a
   batch of conversions.

## Fact-check checklist (reviewer)

- [ ] Every transaction code, command, parameter or setting exists and does what the
      article says. Look it up in vendor documentation; do not trust memory or the LLM.
- [ ] Every error code or message text is real, or the article quotes no code at all.
- [ ] Steps are in a safe order and none needs rights the helpdesk does not have, unless
      the step says who does it.
- [ ] Organisation-specific values (limits, approval rules) are stated as *this
      organisation's* policy, not as vendor defaults.
- [ ] Key facts are atomic, decisive and found in the article body.
- [ ] Nothing in the article answers a *different* topic's question (it would blur the
      gold provenance).

## Week 2 batch: SAP (18 articles, author S, review pending)

These were drafted with AI assistance. The claims below are the ones the reviewer must
verify first, because a wrong one would poison every ticket written from that article:

| Article | Verify |
|---|---|
| SAP-ACC-001 | Profile parameter `login/fails_to_user_lock`; SU01 lock reasons shown on Logon Data |
| SAP-ACC-002 | SU53 shows the last failed authorization check |
| SAP-ACC-004 | Fiori tiles come from business catalogs assigned via PFCG roles |
| SAP-PO-001 | V1 quoted error "ME023"; it could not be verified, so the code was removed and the message described instead |
| SAP-PO-002 | ME28 collective release and ME29N individual release |
| SAP-PO-004 | MRBR releases invoices blocked by MIRO |
| SAP-MAT-004 | Materials-management period: current and previous period open; MMPV and MMRV |
| SAP-INT-001 | SM37 statuses "Released" versus "Ready", SM50 for work processes |
| SAP-INT-002 | IDoc status 51 text; BD87 reprocessing |
| SAP-SYS-001 | Dispatcher port 32 plus instance number |
| SAP-FI-001 | OB08 rates; fallback to the most recent earlier rate; FB08 reversal |
