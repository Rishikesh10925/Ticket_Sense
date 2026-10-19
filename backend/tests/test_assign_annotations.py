"""Annotation tool v1: assignment batches written to the database, served in shuffled
order, and disagreements sent to a third reviewer (docs/annotation-tool.md)."""

import asyncio
import uuid
from collections import Counter

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import settings
from app.core.security import hash_password
from app.models import AnnotationAssignment, Annotator, BenchmarkTicket, Draft, Label, User
from app.scripts import assign_annotations

PASSWORD = "password123"


async def _session():
    engine = create_async_engine(settings.database_url)
    return engine, async_sessionmaker(engine, expire_on_commit=False)


async def _seed(n_drafts: int, n_reviewers: int) -> tuple[list[str], list[str]]:
    engine, session = await _session()
    suffix = uuid.uuid4().hex[:6]
    emails, draft_ids = [], []
    async with session() as db:
        for r in range(n_reviewers):
            user = User(email=f"rev{r}.{suffix}@example.com", full_name=f"Reviewer {r}", role="annotator",
                        hashed_password=hash_password(PASSWORD))
            db.add(user)
            await db.flush()
            db.add(Annotator(user_id=user.id, pseudonym=f"R{r}-{suffix}"))
            emails.append(user.email)
        for i in range(n_drafts):
            ticket = BenchmarkTicket(
                id=f"T{suffix}{i:02d}", benchmark_version="test", group_id=f"G-{i}", subject=f"Issue {i}",
                body="Something is broken.", department=["SAP", "HR", "Cloud"][i % 3], priority="medium",
                type=["A", "B"][i % 2], gold_articles=["X-1"], split="calib",
            )
            db.add(ticket)
            await db.flush()
            draft = Draft(
                benchmark_ticket_id=ticket.id, benchmark_version="test", model="m", prompt_version="draft-v1",
                schema_valid=True, can_answer=True, steps=[{"text": f"Step for {i}.", "citations": [1]}],
                missing_information=[], evidence=[{"n": 1, "article_key": "X-1", "title": "T", "text": "x"}],
                raw_text="{}",
            )
            db.add(draft)
            await db.flush()
            draft_ids.append(str(draft.id))
        await db.commit()
    await engine.dispose()
    return emails, draft_ids


def _login(api, email):
    token = api.post("/auth/login", data={"username": email, "password": PASSWORD}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_plan_writes_a_balanced_double_annotated_batch(api, tmp_path, monkeypatch):
    monkeypatch.setattr(assign_annotations, "SessionLocal", async_sessionmaker(
        create_async_engine(settings.database_url), expire_on_commit=False))
    emails, draft_ids = asyncio.run(_seed(n_drafts=12, n_reviewers=3))
    drafts_file = tmp_path / "drafts.txt"
    drafts_file.write_text("\n".join(draft_ids))

    manifest = asyncio.run(assign_annotations.plan("sprint1", drafts_file, n_overlap=3, seed=11))
    assert manifest["assignments"] == 15  # 9 single + 3 overlap x 2

    async def _rows():
        engine, session = await _session()
        async with session() as db:
            rows = (await db.execute(select(AnnotationAssignment))).scalars().all()
        await engine.dispose()
        return rows

    rows = asyncio.run(_rows())
    per_draft = Counter(r.draft_id for r in rows)
    assert sorted(per_draft.values()).count(2) == 3
    assert max(Counter(r.annotator_id for r in rows).values()) == 5

    # Each reviewer is served their own queue; the API never reveals the overlap flag.
    item = api.get("/annotate/next", headers=_login(api, emails[0])).json()
    assert item is not None and "overlap" not in item and "batch" not in item


def test_disagreeing_overlap_labels_go_to_a_third_reviewer(api, monkeypatch):
    monkeypatch.setattr(assign_annotations, "SessionLocal", async_sessionmaker(
        create_async_engine(settings.database_url), expire_on_commit=False))
    _, draft_ids = asyncio.run(_seed(n_drafts=2, n_reviewers=3))

    async def _label_pair_disagreeing():
        engine, session = await _session()
        async with session() as db:
            annotators = list(await db.scalars(select(Annotator).order_by(Annotator.pseudonym)))
            for annotator, label in zip(annotators[:2], ("A", "W")):
                a = AnnotationAssignment(draft_id=uuid.UUID(draft_ids[0]), annotator_id=annotator.id,
                                         batch="sprint1", overlap=True, position=1)
                db.add(a)
                await db.flush()
                db.add(Label(assignment_id=a.id, label=label, reason_codes=[], time_taken_ms=1000, rubric_version="v1"))
            await db.commit()
            third = annotators[2].id
        await engine.dispose()
        return third

    third = asyncio.run(_label_pair_disagreeing())
    manifest = asyncio.run(assign_annotations.adjudicate("adjud1", seed=5))
    assert manifest["disagreements"] == 1

    async def _adjudications():
        engine, session = await _session()
        async with session() as db:
            rows = (await db.execute(select(AnnotationAssignment).where(AnnotationAssignment.batch == "adjud1"))).scalars().all()
        await engine.dispose()
        return rows

    rows = asyncio.run(_adjudications())
    assert [(str(r.draft_id), r.annotator_id) for r in rows] == [(draft_ids[0], third)]
