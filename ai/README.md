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

## embeddings/embed_resolved_tickets.py

Embeds every `closed` ticket (subject + description) as a second evidence source
alongside the knowledge base. No real resolved-ticket history exists yet, so right now
this means the 120 synthetic tickets from `data/seed_synthetic_tickets.py` — see
[docs/retrieval.md](../docs/retrieval.md).

```bash
uv run --project backend python ../data/seed_synthetic_tickets.py
uv run --project backend python embeddings/embed_resolved_tickets.py
```

## embeddings/retrieve.py

The department-scoped similarity-search retrieval function —
`retrieve_evidence(db, query_text, department_id, k)`, merging both evidence sources,
scoped at the SQL level so there's no cross-department leakage. See
[docs/retrieval.md](../docs/retrieval.md) for how department scoping works and why the
top-k merge is correct. This is the function
`backend/app/services/retrieval.py` imports (Week 5, Rishikesh).

## embeddings/evaluate_retrieval.py

Recall@K evaluation against 15 hand-labelled test queries (3 per department). Current
result: Recall@3 = 15/15 = 1.00 — see [docs/retrieval.md](../docs/retrieval.md) for the
honest read of what a perfect score does and doesn't mean at this corpus size.

```bash
uv run --project backend python embeddings/evaluate_retrieval.py
```

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
`classify_ticket(subject, description)` — the function the `classify` node in
`graph/nodes.py` calls (Week 6, Rishikesh; superseded the Week 4
`backend/app/services/classification.py`, since deleted).

## generation/

Draft generation: `llm_interface.py` (the `LLMProvider` abstraction + the default
`StubLLMProvider`, extractive not generative — **no paid LLM API key is available**,
see [docs/draft-generation.md](../docs/draft-generation.md) before reading too much
into groundedness results), `prompt.py` (builds the grounded, cited-answer prompt),
and `groundedness.py` (verifies every citation maps to a real evidence item). See
[docs/groundedness-review.md](../docs/groundedness-review.md) for the manual review of
generated drafts (10/10 fully grounded — with the caveat that a fully honest read of
what that does and doesn't mean is in the docs, not just the number).

```python
from generation.prompt import build_prompt
from generation.llm_interface import StubLLMProvider

prompt = build_prompt(ticket.subject, ticket.description, evidence)
draft = StubLLMProvider().generate(prompt, evidence)
```

`generation/provider_factory.py` adds `get_llm_provider(name)`, a config-driven lookup
(`LLM_PROVIDER` in `.env`, only `"stub"` registered today) so callers never construct a
provider class directly — see [docs/langgraph-pipeline.md](../docs/langgraph-pipeline.md).

## graph/

The LangGraph pipeline (Week 6, Rishikesh; extended Week 7 for attachment text,
extended Week 8 for confidence scoring, extended Week 9 for the confidence gate) that
wires extraction → classification → routing → retrieval → confidence scoring → a
gate deciding whether to draft or escalate into a single `StateGraph`: `state.py` (the
`TicketState` TypedDict threaded between nodes), `nodes.py` (node factories —
`make_extract_node`, `make_classify_node`, `make_route_node`, `make_retrieve_node`,
`make_score_node`, `make_draft_node`, `make_escalate_node`, plus `gate_condition` — the
conditional-edge function the gate itself is, not a node — each closing over the
per-run DB session/LLM provider it needs rather than putting them in graph state; also
`_augmented_description(state)`, which folds extracted attachment text into what
classify/retrieve/draft actually read), and `pipeline.py`
(`build_pipeline(db, department_model, llm_provider, default_confidence_threshold)`,
which builds and compiles the graph, `score` now running before `draft` — see
docs/langgraph-pipeline.md for why). `backend/app/services/pipeline.py` is what calls
this against a real ticket and persists the result. See
[docs/langgraph-pipeline.md](../docs/langgraph-pipeline.md).

## ocr/

Attachment text extraction (Week 7, Shivaganesh): `extract.py` exposes
`extract_attachment_text(path, attachment_type)`, dispatching to `extract_from_image`
(EasyOCR — a per-process lazy-loaded `Reader`, same pattern as
`embeddings/retrieve.py`'s `SentenceTransformer`), `extract_from_pdf` (`pypdf`'s text
layer, not OCR), or `extract_from_log` (plain read). All three return an
`ExtractionResult(text, confidence)` — `confidence` is EasyOCR's average per-detection
score for images, `None` for PDF/log since a direct text read isn't a probabilistic
extraction. See [docs/ocr-evaluation.md](../docs/ocr-evaluation.md) for quality notes
and known limitations on the hand-crafted sample screenshots in
`data/sample_screenshots/` (`data/make_sample_screenshots.py`).

```python
from ocr.extract import extract_attachment_text

result = extract_attachment_text(ticket.attachment_path, ticket.attachment_type)
print(result.text, result.confidence)
```

## confidence/

The confidence classifier (Week 8, Shivaganesh) — an independent model that scores a
generated draft on external reliability signals, never the LLM's own self-assessment
(see [docs/architecture.md](../docs/architecture.md)). `features.py` computes the five
signals (`retrieval_relevance`, `ticket_resolution_similarity`, `document_freshness`,
`ocr_confidence`, `category_risk` — the last one derived from the department
classifier's own measured per-department F1, see
[docs/classification-metrics.md](../docs/classification-metrics.md)) into a
`ConfidenceFeatures` dataclass. `synthetic_labels.py` bootstraps training labels with a
documented, explicitly-not-real-data formula, since no real human review outcomes
exist yet — see [docs/confidence-model.md](../docs/confidence-model.md)'s "What the
synthetic labels are (and aren't)" before trusting this model's accuracy against real
outcomes. `train.py` builds a dataset from real retrieval against the 120 synthetic
historical tickets and trains a `LogisticRegression`; `predict.py` loads the saved
artifact and exposes `predict_confidence(features) -> float`.

```python
from confidence.features import compute_features
from confidence.predict import predict_confidence

features = compute_features(evidence, ticket.ocr_confidence, department_name)
score = predict_confidence(features)
```

Initial evaluation: accuracy 0.54, ROC-AUC 0.605 on a 96/24 train/test split — see
[docs/confidence-metrics.md](../docs/confidence-metrics.md) for the full table and
[docs/confidence-model.md](../docs/confidence-model.md) for the honest read of what
that does and doesn't demonstrate yet.
