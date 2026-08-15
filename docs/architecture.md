# Architecture

## Why a separate confidence classifier, not LLM self-confidence

LLMs are poorly calibrated when asked to self-rate their own answers — they tend to be
confidently wrong, especially on out-of-distribution tickets. A separately trained
classifier that consumes *external* signals about the specific retrieval-and-draft that
just happened is far more trustworthy, and — critically — it can be retrained on real
human Accept/Edit/Reject/Escalate outcomes over time, so it gets better as the system is
used. That feedback loop (draft → human decision → logged outcome → retraining) is what
makes this a research contribution rather than a plain RAG chatbot.

## Data flow

1. **Intake** — a ticket (text + optional image/PDF/log attachment) is submitted by an
   End User.
2. **Classification** — department, priority, and sentiment are predicted (classification
   model, not the confidence model).
3. **Retrieval** — the ticket is embedded and matched against `embeddings` rows scoped to
   the ticket's department, pulling candidate `knowledge_base` chunks.
4. **Drafting** — the LLM (behind the `LLMProvider` interface in
   `ai/agents/llm_interface.py`) drafts a reply constrained to only the retrieved
   evidence, with citations.
5. **Confidence scoring** — the confidence classifier scores the draft using: retrieval
   relevance, ticket-to-resolution similarity, knowledge-base document freshness, OCR
   confidence (if the ticket had an image/PDF attachment), and category risk. This
   feature vector is snapshotted into `tickets.confidence_features` (JSONB) so it can
   later be joined against the human outcome for retraining.
6. **Routing** — above the confidence threshold, the ticket goes to a Department Engineer
   for review (Accept/Edit/Reject); below it, the ticket is escalated untouched
   (`escalations` table) with the reason and score recorded.
7. **Feedback** — every reviewer action is logged to `feedback`, and a corresponding
   `ticket_history` entry records the state transition. These logs are the training data
   for the next confidence-model iteration.

## Schema rationale

- **UUID primary keys** everywhere (`pgcrypto`'s `gen_random_uuid()`) — avoids leaking
  sequential counts and is the more conventional choice for a system that will eventually
  export ticket/feedback data for model training.
- **`tickets.confidence_features` (JSONB)** exists specifically so a training pipeline can
  reconstruct "what did the confidence model see" for any historical ticket without
  re-deriving retrieval/OCR/freshness signals after the fact.
- **`knowledge_base` has no stored freshness score** — freshness is derived from
  `updated_at` at feature-computation time rather than duplicated as a column that could
  drift out of sync.
- **`embeddings.embedding` is `VECTOR(384)`**, matching `sentence-transformers/all-MiniLM-L6-v2`
  (`EMBEDDING_DIM` in `.env`). pgvector columns are fixed-dimension; switching embedding
  models later means a migration that recreates this column and re-embeds the knowledge
  base, not a config change. This is an accepted tradeoff for v1.
- **`ticket_history.detail` (JSONB)** is a flexible free-form payload (old/new values,
  etc.) rather than a fixed-column audit table — deliberately lightweight since full
  audit-log infrastructure is out of scope for v1.

## Resolved decisions

- **No ANN index on `embeddings` yet — exact search until the table is large enough to
  need one.** The original migration created an `ivfflat` index with `lists = 100`. Once
  the embeddings table was actually populated (48 rows from the seeded KB), that index
  produced *wrong* results: with far under 1 row per list, `ivfflat`'s default
  `probes = 1` searches a single near-empty cluster, so a query for "ME023 error" missed
  the ME023 article entirely and returned unrelated ones instead. Migration `0002` drops
  the index; pgvector's `<=>` operator does an exact sequential scan without one, which
  is both correct and plenty fast at hundreds-to-low-thousands of rows. Re-add an ANN
  index (ivfflat or hnsw) once the table is large enough that a sequential scan is
  actually slow, with `lists`/`m` tuned to the real row count at that time — don't just
  restore the old parameters.
- **`ai/` packaging: one shared virtual environment, not a separate venv.** `ai/` is a
  path dependency of `backend/` — its extras (`datasets`, `sentence-transformers`,
  `scikit-learn`, `langgraph`) live in `backend/pyproject.toml`'s single `ai` optional-
  dependency group — rather than getting its own uv project. Reason: for a 3-person team
  on a semester timeline, one dependency tree is simpler to install, lock, and keep in
  sync than two — no risk of `backend/` and `ai/` drifting onto incompatible versions of
  shared libraries, and no "which venv do I activate" friction for whoever picks up a
  task. If `ai/`'s dependencies (`torch` via sentence-transformers, etc.) later prove
  heavy enough to slow down backend installs, or someone wants to deploy/scale it
  independently, split it into its own venv/service then — this is the starting default,
  not a permanent constraint.
- **Auth: JWT via `bcrypt` + `PyJWT`, not `passlib`/sessions.** `passlib` has an
  unresolved bcrypt-backend maintenance issue, so password hashing calls `bcrypt`
  directly (`app/core/security.py`). Stateless JWT (not server-side sessions) since
  there's no infra for a session store in scope (explicitly no Redis). Registration
  (`POST /api/auth/register`) is **End User only** — Department Engineer / Admin accounts
  are created via the seed/admin path, not self-service, matching a realistic enterprise
  flow without building a user-admin UI that's out of v1 scope. No schema change was
  needed — `users.hashed_password`/`role` already supported this from Phase 1.
- **Classifier: 3 independent scikit-learn pipelines, not one multi-output model.**
  `ai/models/train_classifier.py` trains separate `TfidfVectorizer` + `LogisticRegression`
  pipelines for department, priority, and sentiment, since the three targets have
  unrelated label spaces. Still counts as one of the project's 2 allowed models — the
  brief bundles department/priority/sentiment as one classification capability, distinct
  from the separate confidence/escalation model.

## Known limitation: priority/sentiment classification quality

Trained on the ~96-row synthetic set (`data/synthetic_labeled_tickets.py`): **department
classification is solid (85% test accuracy)** — departments have strongly distinctive
vocabulary (ME023/IDoc vs. VPN/wifi vs. S3/EC2 vs. leave/payslip), which bag-of-words
TF-IDF picks up easily even with little data. **Priority classification is currently
unusable (15% accuracy, worse than the 25% random baseline for 4 classes)** — priority is
a tone/urgency signal, not a vocabulary signal, and TF-IDF word-presence features barely
capture it with this few examples. **Sentiment is weak but real (40% vs. 33% random)**,
hurt by only 12 "positive"-labeled tickets total. Before this classifier is trusted for
anything beyond proving the pipeline shape: either grow the labeled set substantially, or
give priority a different feature approach entirely (explicit urgency keyword/rule
features, not just TF-IDF).

## Open decisions (deferred, not forgotten)

- **LLM provider** — stubbed behind `ai/agents/llm_interface.py`'s `LLMProvider`
  interface (`StubLLMProvider` is the only implementation so far). Provider choice is a
  separate conversation. Blocks `draft_node` in `ai/graph/nodes.py`, which is currently
  a `NotImplementedError` stub.
- **Confidence/escalation model** — not started. Blocks `score_node` in
  `ai/graph/nodes.py`, also currently a stub.
