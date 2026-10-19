"""Offline feature pipeline: a features-v1 signal vector for every benchmark draft
(Roadmap Week 7, Shivaganesh: "offline feature pipeline for all tickets, all groups").

    python ai/signals/build_features.py --version v1

Reads only what the live pipeline would have had at decision time: the draft, its claim
scores, its logged retrieval run (every candidate with its ranks and scores), the cited
articles' dates, and classifier v2's prediction on the redacted ticket. Labels are never
read. Evidence age is measured from the benchmark freeze date, not from today, so the
features do not drift with the calendar. Resumable: drafts that already have a
features-v1 vector are skipped.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "ai"))

from security.pii import redact  # noqa: E402
from signals.features import FEATURE_VERSION, Candidate, SignalInput, extract  # noqa: E402


def freeze_date(version: str) -> datetime:
    record = json.loads((ROOT / "data" / "benchmark" / f"FREEZE_{version}.json").read_text(encoding="utf-8"))
    return datetime.fromisoformat(record["frozen_on"]).replace(tzinfo=timezone.utc)


async def run(version: str, limit: int | None) -> int:
    from sqlalchemy import select

    from app.database import SessionLocal
    from app.models import BenchmarkTicket, Draft, KnowledgeBase, SignalVector
    from app.models.retrieval_run import RetrievalHit, RetrievalRun
    from graph.nodes import _classifier_v2, _uncertainty

    classifier = _classifier_v2()
    now = freeze_date(version)
    written = 0
    async with SessionLocal() as db:
        have = select(SignalVector.draft_id).where(SignalVector.feature_version == FEATURE_VERSION)
        rows = (
            await db.execute(
                select(Draft, BenchmarkTicket, RetrievalRun)
                .join(BenchmarkTicket, (BenchmarkTicket.id == Draft.benchmark_ticket_id)
                      & (BenchmarkTicket.benchmark_version == Draft.benchmark_version))
                .join(RetrievalRun, RetrievalRun.id == Draft.retrieval_run_id)
                .where(Draft.benchmark_version == version, Draft.id.not_in(have))
                .order_by(Draft.benchmark_ticket_id)
            )
        ).all()[: limit or None]
        print(f"{len(rows)} drafts need a {FEATURE_VERSION} vector", flush=True)
        started = time.perf_counter()
        for i, (draft, ticket, run_row) in enumerate(rows, start=1):
            hits = (
                await db.execute(
                    select(RetrievalHit, KnowledgeBase.article_key, KnowledgeBase.updated_at)
                    .join(KnowledgeBase, KnowledgeBase.id == RetrievalHit.knowledge_base_id)
                    .where(RetrievalHit.run_id == run_row.id)
                )
            ).all()
            candidates = [
                Candidate(key, h.keyword_rank, h.dense_rank, h.dense_score, h.fused_score, h.rerank_score,
                          h.final_rank, updated, h.text)
                for h, key, updated in hits
            ]
            mapping: dict[str, str] = {}
            subject = redact(ticket.subject, mapping).text
            body = redact(ticket.body, mapping).text
            attachment = redact(ticket.attachment_text, mapping).text or None
            text = f"{subject}\n\n{body}"
            classified = text + (f"\n\n[Extracted from attachment]\n{attachment}" if attachment else "")
            prediction = classifier.predict([classified])[0]
            await db.refresh(draft, ["claims"])
            features = extract(
                SignalInput(
                    candidates=candidates,
                    steps=draft.steps,
                    claims=[{"support": c.support, "cited": c.cited} for c in draft.claims],
                    can_answer=draft.can_answer,
                    schema_valid=draft.schema_valid,
                    missing_information=draft.missing_information,
                    ticket_text=text,
                    attachment_text=attachment,
                    probe_top1=run_row.probe_top1_similarity,
                    classification={"department": _uncertainty(prediction["department"])},
                    now=now,
                )
            )
            db.add(SignalVector(draft_id=draft.id, feature_version=FEATURE_VERSION, features=features))
            written += 1
            if i % 100 == 0 or i == len(rows):
                await db.commit()
                print(f"{i}/{len(rows)} ({i / (time.perf_counter() - started) * 60:.0f}/min)", flush=True)
        await db.commit()
    return written


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--version", default="v1")
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()
    print(f"wrote {asyncio.run(run(args.version, args.limit))} vectors")


if __name__ == "__main__":
    main()
