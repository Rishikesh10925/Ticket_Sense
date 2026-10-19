"""Persist a retrieval run with every candidate's scores (migration 0013), and read the
logged evidence back so the UI shows exactly what the pipeline used."""

from __future__ import annotations

import sys
import uuid
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # ai/

from embeddings.retrieve import EvidenceResult  # noqa: E402

from app.models import KnowledgeBase, RetrievalHit, RetrievalRun  # noqa: E402
from retrieval.hybrid import RetrievalResult  # noqa: E402

CONFIG_VERSION = "hybrid-v1"  # keyword+dense, RRF k=60, MiniLM-L6 rerank of top 20


async def log_run(
    db: AsyncSession, result: RetrievalResult, ticket_id: uuid.UUID | None, mode: str = "hybrid", reranked: bool = True
) -> RetrievalRun:
    run = RetrievalRun(
        ticket_id=ticket_id,
        department_id=result.department_id,
        query_text=result.query,
        mode=mode,
        reranked=reranked,
        config_version=CONFIG_VERSION,
        probe_top1_similarity=result.probe_top1_similarity,
        probe_department_id=result.probe_department_id,
        latency_ms={k: round(v, 1) for k, v in result.latency_ms.items()},
    )
    db.add(run)
    await db.flush()
    final_rank = {h.chunk_id: i for i, h in enumerate(result.hits, start=1)}
    for hit in result.candidates:
        db.add(
            RetrievalHit(
                run_id=run.id,
                chunk_id=hit.chunk_id,
                knowledge_base_id=hit.article_id,
                final_rank=final_rank.get(hit.chunk_id),
                keyword_rank=hit.keyword_rank,
                keyword_score=hit.keyword_score,
                dense_rank=hit.dense_rank,
                dense_score=hit.dense_score,
                fused_score=hit.fused_score,
                rerank_score=hit.rerank_score,
                text=hit.text,
            )
        )
    await db.flush()
    return run


def to_evidence(result: RetrievalResult) -> list[EvidenceResult]:
    """Final hits in the evidence shape the drafting and V1 scoring code already use.
    `distance` is cosine distance (1 - similarity); a keyword-only hit has no dense
    score and gets the worst distance in the list."""
    worst = max((1 - h.dense_score for h in result.hits if h.dense_score is not None), default=1.0)
    return [
        EvidenceResult(
            source_type="knowledge_base",
            source_id=h.article_id,
            title=h.title,
            snippet=h.text,
            department_id=result.department_id,
            distance=(1 - h.dense_score) if h.dense_score is not None else worst,
            **({"updated_at": h.updated_at} if h.updated_at else {}),
        )
        for h in result.hits
    ]


async def logged_evidence(db: AsyncSession, ticket_id: uuid.UUID) -> list[EvidenceResult]:
    """Evidence from the ticket's most recent logged run, in final rank order."""
    run = await db.scalar(
        select(RetrievalRun).where(RetrievalRun.ticket_id == ticket_id).order_by(RetrievalRun.created_at.desc()).limit(1)
    )
    if run is None:
        return []
    rows = (
        await db.execute(
            select(RetrievalHit, KnowledgeBase)
            .join(KnowledgeBase, KnowledgeBase.id == RetrievalHit.knowledge_base_id)
            .where(RetrievalHit.run_id == run.id, RetrievalHit.final_rank.is_not(None))
            .order_by(RetrievalHit.final_rank)
        )
    ).all()
    return [
        EvidenceResult(
            source_type="knowledge_base",
            source_id=kb.id,
            title=kb.title,
            snippet=hit.text,
            department_id=run.department_id,
            distance=(1 - hit.dense_score) if hit.dense_score is not None else 1.0,
            updated_at=kb.updated_at,
        )
        for hit, kb in rows
    ]
