# Retrieval pipeline

Week 5 note (Shivaganesh) on department-scoped similarity-search retrieval over the
knowledge base and resolved tickets — the evidence source `backend/app/services/
retrieval.py` (Week 5, Rishikesh) and the Engineer's evidence panel (Week 5, Aashritha)
both build on.

## Two evidence sources

1. **Knowledge base** — the 60 authored articles (`db/seed/knowledge_base/`), embedded
   by `ai/embeddings/embed_knowledge_base.py` since Week 3.
2. **Resolved tickets** — new this week. No real resolved-ticket history exists yet
   (the review/drafting workflow that would produce one isn't built until a later
   week), so this embeds the 120 synthetic tickets from Week 4
   (`data/seed_synthetic_tickets.py` inserts them as `closed` tickets attributed to a
   placeholder account; `ai/embeddings/embed_resolved_tickets.py` embeds anything with
   `status = 'closed'`, so it keeps working once real tickets close). This is
   synthetic data standing in for a real evidence source, not a claim that these are
   real historical resolutions — worth remembering when reading a "similar past ticket"
   result in the evidence panel.

Both sources needed the `embeddings` table to support two kinds of parent row instead
of one — `knowledge_base_id` is now nullable, a new nullable `ticket_id` was added, and
a check constraint (`ck_embeddings_exactly_one_source`) enforces exactly one is set per
row (migration `0003`).

## Department scoping

`ai/embeddings/retrieve.py`'s `retrieve_evidence(db, query_text, department_id, k)`
filters at the SQL level — the KB branch joins on `knowledge_base.department_id`, the
ticket branch joins on `tickets.department_id`, both in the `WHERE` clause before any
ranking happens. A query scoped to HR cannot see Networking content because the rows
never enter the candidate set, not because of app-level filtering afterward. Verified
directly: the same query ("VPN not connecting from home") scoped to Networking returns
VPN-relevant results with cosine distances of 0.20–0.54; scoped to HR, the best result
is 0.80 — nothing HR-related is semantically close to a VPN query, so this also serves
as an informal check that there's no leakage, ahead of the Week 5 Team Integration
check that does this formally across all five departments.

Merging the two sources (KB top-k and ticket top-k, re-sorted, sliced to k) is correct
for the combined top-k: any result in the true top-k of the union must be within the
top-k of whichever source it came from, since fewer than k items from its own source
could out-rank it.

## Recall@K evaluation

`ai/embeddings/evaluate_retrieval.py` — 15 hand-authored test queries, 3 per
department, each paired with the exact KB article title it should retrieve. Queries are
phrased the way an End User would actually write a ticket, not copied from the article's
own title/text (e.g. "I keep getting ME023 error when trying to post a goods receipt"
for the "ME023: Purchase Order Item Blocked" article), so the test measures semantic
retrieval, not string matching.

**Result: Recall@3 = 15/15 = 1.00, across all five departments.**

### Honest read of a perfect score

A perfect Recall@3 on 15 queries is a real result, not a mistake, but it should not be
over-read as "retrieval is solved." It reflects the corpus this week's evaluation ran
against: 12 articles per department, each covering a distinct, non-overlapping problem
(SAP's ME023 error and locked-account issue are semantically nothing alike). At this
size and this level of topic separation, a competent embedding model is expected to
retrieve the right article almost every time — the test isn't yet stressing the
retrieval with harder cases: queries near a department's decision boundary, articles
that are topically similar to each other within the same department, or a genuinely
ambiguous ticket. Recall@K should be re-measured as the knowledge base grows and starts
to include closer near-duplicates, where a perfect score would actually mean something
harder-won.

## What's not built yet

- The live API endpoint that calls `retrieve_evidence` for a given ticket
  (Week 5, Rishikesh — `backend/app/services/retrieval.py`).
- The evidence-display panel on the Engineer's ticket detail screen
  (Week 5, Aashritha).
- pgvector ANN indexes (`ivfflat`/`hnsw`) — still exact search, per
  `architecture.md`'s "Resolved decisions" note: not worth an approximate index until
  the embeddings table is large enough that a sequential scan is actually slow. At 180
  rows, it isn't.
