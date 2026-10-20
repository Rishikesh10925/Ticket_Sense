"""Hybrid retrieval: keyword + dense search, reciprocal rank fusion, cross-encoder rerank
(Blueprint V2 §12.1; Roadmap Week 4).

Both searches run over `kb_chunks` joined to `knowledge_base`, with the department filter
and `served = true` inside the SQL, so a ticket can never retrieve another department's
content or a withheld article. A separate cross-department probe records how well the
best *other* department would have matched (a routing-error signal, §13.2). It is
returned only as a score and never as evidence.

    candidates   top 20 by full text (ts_rank_cd)  +  top 20 by cosine distance
    fusion       reciprocal rank fusion, k = 60 [Cormack et al. 2009]
    rerank       cross-encoder over the top 20 fused chunks, keep top 5 [Nogueira & Cho 2019]
"""

from __future__ import annotations

import re
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from functools import lru_cache

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
RERANK_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
N_CANDIDATES = 20
RRF_K = 60
_WORD = re.compile(r"[a-z0-9]{2,}")


@dataclass
class Hit:
    chunk_id: uuid.UUID
    article_id: uuid.UUID
    article_key: str | None
    title: str
    text: str
    updated_at: datetime | None
    keyword_rank: int | None = None
    keyword_score: float | None = None
    dense_rank: int | None = None
    dense_score: float | None = None  # cosine similarity
    fused_score: float = 0.0
    rerank_score: float | None = None


@dataclass
class RetrievalResult:
    query: str
    department_id: uuid.UUID
    hits: list[Hit]  # final top-k, reranked
    candidates: list[Hit] = field(default_factory=list)  # all fused candidates, for logging
    probe_top1_similarity: float | None = None  # best dense match in any OTHER department
    probe_department_id: uuid.UUID | None = None
    latency_ms: dict[str, float] = field(default_factory=dict)

    def ranked_article_keys(self) -> list[str]:
        """Distinct article keys in final order, for article-level metrics."""
        return list(dict.fromkeys(h.article_key for h in self.hits if h.article_key))


@lru_cache(maxsize=1)
def _embedder():
    from sentence_transformers import SentenceTransformer

    from devices import device

    return SentenceTransformer(EMBED_MODEL, device=device("embed"))


@lru_cache(maxsize=1)
def _reranker():
    from sentence_transformers import CrossEncoder

    from devices import device

    return CrossEncoder(RERANK_MODEL, device=device("rerank"))


def or_tsquery(query: str) -> str:
    """Tickets are natural language, so all-terms (AND) matching finds almost nothing.
    Match any term and let ts_rank_cd reward chunks that contain more of them."""
    words = list(dict.fromkeys(_WORD.findall(query.lower())))
    return " | ".join(words[:64])


_KEYWORD_SQL = text(
    """
    SELECT c.id, c.knowledge_base_id, kb.article_key, kb.title, c.text, kb.updated_at,
           ts_rank_cd(c.tsv, q) AS score
    FROM kb_chunks c
    JOIN knowledge_base kb ON kb.id = c.knowledge_base_id,
         to_tsquery('english', :tsq) q
    WHERE kb.department_id = :dept AND kb.served AND c.tsv @@ q
    ORDER BY score DESC, c.id
    LIMIT :n
    """
)
_DENSE_SQL = text(
    """
    SELECT c.id, c.knowledge_base_id, kb.article_key, kb.title, c.text, kb.updated_at,
           1 - (c.embedding <=> CAST(:qv AS vector)) AS score
    FROM kb_chunks c
    JOIN knowledge_base kb ON kb.id = c.knowledge_base_id
    WHERE kb.department_id = :dept AND kb.served
    ORDER BY c.embedding <=> CAST(:qv AS vector), c.id
    LIMIT :n
    """
)
_PROBE_SQL = text(
    """
    SELECT kb.department_id, 1 - (c.embedding <=> CAST(:qv AS vector)) AS score
    FROM kb_chunks c
    JOIN knowledge_base kb ON kb.id = c.knowledge_base_id
    WHERE kb.department_id <> :dept AND kb.served
    ORDER BY c.embedding <=> CAST(:qv AS vector)
    LIMIT 1
    """
)


def rrf(rank_lists: list[list[uuid.UUID]], k: int = RRF_K) -> dict[uuid.UUID, float]:
    scores: dict[uuid.UUID, float] = {}
    for ranks in rank_lists:
        for position, item in enumerate(ranks, start=1):
            scores[item] = scores.get(item, 0.0) + 1.0 / (k + position)
    return scores


async def hybrid_search(
    db: AsyncSession,
    query: str,
    department_id: uuid.UUID,
    k: int = 5,
    rerank: bool = True,
    mode: str = "hybrid",
) -> RetrievalResult:
    """mode: "hybrid" (keyword + dense, fused), "keyword" or "dense" (for ablations)."""
    if mode not in ("hybrid", "keyword", "dense"):
        raise ValueError(f"unknown retrieval mode {mode!r}")
    timings: dict[str, float] = {}
    t0 = time.perf_counter()
    qv = _embedder().encode(query, normalize_embeddings=True).tolist()
    qv_literal = "[" + ",".join(f"{x:.6f}" for x in qv) + "]"
    timings["embed"] = (time.perf_counter() - t0) * 1000

    t0 = time.perf_counter()
    hits: dict[uuid.UUID, Hit] = {}
    tsq = or_tsquery(query)
    keyword_rows = (
        (await db.execute(_KEYWORD_SQL, {"tsq": tsq, "dept": department_id, "n": N_CANDIDATES})).all()
        if tsq and mode != "dense"
        else []
    )
    dense_rows = (
        (await db.execute(_DENSE_SQL, {"qv": qv_literal, "dept": department_id, "n": N_CANDIDATES})).all()
        if mode != "keyword"
        else []
    )
    probe = (await db.execute(_PROBE_SQL, {"qv": qv_literal, "dept": department_id})).first()
    timings["search"] = (time.perf_counter() - t0) * 1000

    for rank, row in enumerate(keyword_rows, start=1):
        hit = hits.setdefault(row.id, Hit(row.id, row.knowledge_base_id, row.article_key, row.title, row.text, row.updated_at))
        hit.keyword_rank, hit.keyword_score = rank, float(row.score)
    for rank, row in enumerate(dense_rows, start=1):
        hit = hits.setdefault(row.id, Hit(row.id, row.knowledge_base_id, row.article_key, row.title, row.text, row.updated_at))
        hit.dense_rank, hit.dense_score = rank, float(row.score)

    fused = rrf([[r.id for r in keyword_rows], [r.id for r in dense_rows]])
    for chunk_id, score in fused.items():
        hits[chunk_id].fused_score = score
    candidates = sorted(hits.values(), key=lambda h: (-h.fused_score, str(h.chunk_id)))[:N_CANDIDATES]

    t0 = time.perf_counter()
    if rerank and candidates:
        scores = _reranker().predict([(query, h.text) for h in candidates])
        for hit, score in zip(candidates, scores):
            hit.rerank_score = float(score)
        final = sorted(candidates, key=lambda h: (-(h.rerank_score or 0.0), str(h.chunk_id)))[:k]
    else:
        final = candidates[:k]
    timings["rerank"] = (time.perf_counter() - t0) * 1000

    return RetrievalResult(
        query=query,
        department_id=department_id,
        hits=final,
        candidates=candidates,
        probe_top1_similarity=float(probe.score) if probe else None,
        probe_department_id=probe.department_id if probe else None,
        latency_ms=timings,
    )
