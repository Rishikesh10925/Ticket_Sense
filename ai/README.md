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

## What's not here yet

Retrieval (querying `embeddings` for a given ticket), the LangGraph pipeline, and
classifier training are all planned for later weeks — see the root
[README.md](../README.md) Project status.
