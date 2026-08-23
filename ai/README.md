# ai/

## embeddings/embed_knowledge_base.py

Generates embeddings for the authored knowledge-base articles in
`db/seed/knowledge_base/`, using `sentence-transformers/all-MiniLM-L6-v2` (384-dim,
matching `backend/app/models/embedding.py`). Upserts into the `knowledge_base` and
`embeddings` tables — safe to re-run.

```bash
cd backend
uv sync --extra ai
cd ..
uv run --project backend python ai/embeddings/embed_knowledge_base.py
```

Requires `db` running and migrated (`uv run alembic upgrade head` from `backend/`).

Kept out of the default backend install (`sentence-transformers` pulls in `torch`) — see
`backend/pyproject.toml`'s `ai` optional-dependency group and
[docs/architecture.md](../docs/architecture.md)'s "ai/ packaging" note for why this
lives here rather than as a separate project.

## models/

Trains and packages the department/priority/sentiment classifiers. See
[docs/classification-model.md](../docs/classification-model.md) for methodology and
honest limitations, and [docs/classification-metrics.md](../docs/classification-metrics.md)
for the current precision/recall/F1 numbers.

```bash
python ../data/synthetic_labeled_tickets.py   # -> data/processed/synthetic_tickets.csv
cd ../backend && uv sync --extra ai && cd ../ai
uv run --project ../backend python models/train_classifier.py
```

Saves trained pipelines to `models/artifacts/*.joblib` (committed — small, and the live
pipeline needs them at runtime). `models/classifier.py` loads them and exposes
`classify_ticket(subject, description)` — the function
`backend/app/services/classification.py` imports (Week 4, Rishikesh).

## What's not here yet

Retrieval (querying `embeddings` for a given ticket) and the LangGraph pipeline are
planned for later weeks — see the root [README.md](../README.md) Project status.
