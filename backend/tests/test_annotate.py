"""Annotation tool v0 (docs/annotation-tool.md): blinding, ordering, final labels."""

import asyncio
import json
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import settings
from app.core.security import hash_password
from app.models import AnnotationAssignment, Annotator, BenchmarkTicket, Draft, Label, User

PASSWORD = "password123"
FORBIDDEN = ("confidence", "score", "lane", "signal", "model", "type", "gold", "split", "overlap", "batch", "priority")


async def _seed(n_items: int = 2) -> dict:
    engine = create_async_engine(settings.database_url)
    session = async_sessionmaker(engine, expire_on_commit=False)
    async with session() as db:
        suffix = uuid.uuid4().hex[:6]
        user = User(email=f"rev.{suffix}@example.com", full_name="Reviewer", role="annotator",
                    hashed_password=hash_password(PASSWORD))
        db.add(user)
        await db.flush()
        annotator = Annotator(user_id=user.id, pseudonym=f"REV-{suffix}")
        db.add(annotator)
        await db.flush()
        assignment_ids = []
        for i in range(n_items):
            ticket = BenchmarkTicket(
                id=f"T-{suffix}{i}", benchmark_version="test", group_id="G-1", subject=f"VPN issue {i}",
                body="VPN hangs at connecting.", department="Networking", priority="high", type="A",
                gold_articles=["NET-VPN-001"], split="calib",
            )
            db.add(ticket)
            await db.flush()
            draft = Draft(
                benchmark_ticket_id=ticket.id, benchmark_version="test", model="qwen2.5:7b-instruct",
                prompt_version="draft-v1", schema_valid=True, can_answer=True,
                steps=[{"text": "Try a mobile hotspot.", "citations": [1]}], missing_information=[],
                evidence=[{"n": 1, "article_key": "NET-VPN-001", "title": "VPN client not connecting",
                           "text": "Retry from a mobile hotspot."}],
                raw_text="{}", groundedness=0.9,
            )
            db.add(draft)
            await db.flush()
            # Inserted in reverse so ordering must come from `position`, not insertion.
            a = AnnotationAssignment(draft_id=draft.id, annotator_id=annotator.id, batch="pilot",
                                     overlap=True, position=n_items - i)
            db.add(a)
            await db.flush()
            assignment_ids.append(str(a.id))
        await db.commit()
    await engine.dispose()
    return {"email": user.email, "assignments": assignment_ids}


def _login(api, email):
    return {"Authorization": f"Bearer {api.post('/auth/login', data={'username': email, 'password': PASSWORD}).json()['access_token']}"}


def _keys(obj, prefix=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield k
            yield from _keys(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _keys(v)


def test_next_item_is_blinded_and_ordered_by_position(api):
    seeded = asyncio.run(_seed())
    headers = _login(api, seeded["email"])
    resp = api.get("/annotate/next", headers=headers)
    assert resp.status_code == 200
    item = resp.json()
    # The item with the lowest position (inserted last) comes first.
    assert item["assignment_id"] == seeded["assignments"][-1]
    assert item["progress"] == {"done": 0, "total": 2}
    leaked = [f for f in FORBIDDEN if any(f in k for k in _keys(item))]
    assert leaked == [], f"blinding broken, payload carries {leaked}"
    assert "NET-VPN-001" not in json.dumps(item)  # gold article id never shown
    assert item["draft"]["steps"] and item["evidence"]


def test_label_is_final_and_progress_advances(api):
    seeded = asyncio.run(_seed())
    headers = _login(api, seeded["email"])
    first = api.get("/annotate/next", headers=headers).json()["assignment_id"]
    body = {"label": "M", "reason_codes": ["formatting"], "time_taken_ms": 41000}
    resp = api.post(f"/annotate/{first}", json=body, headers=headers)
    assert resp.status_code == 201 and resp.json()["progress"] == {"done": 1, "total": 2}
    assert api.post(f"/annotate/{first}", json=body, headers=headers).status_code == 409
    second = api.get("/annotate/next", headers=headers).json()["assignment_id"]
    assert second != first
    skip = {"skipped_reason": "unreadable", "time_taken_ms": 5000}
    assert api.post(f"/annotate/{second}", json=skip, headers=headers).status_code == 201
    assert api.get("/annotate/next", headers=headers).json() is None

    async def _labels():
        engine = create_async_engine(settings.database_url)
        async with async_sessionmaker(engine)() as db:
            rows = list(await db.scalars(select(Label)))
        await engine.dispose()
        return rows

    labels = asyncio.run(_labels())
    assert {(lb.label, lb.acceptable) for lb in labels} == {("M", True), (None, None)}
    assert all(lb.rubric_version == "v1" for lb in labels)


def test_label_validation(api):
    seeded = asyncio.run(_seed(1))
    headers = _login(api, seeded["email"])
    aid = seeded["assignments"][0]
    assert api.post(f"/annotate/{aid}", json={"label": "X", "time_taken_ms": 1}, headers=headers).status_code == 422
    both = {"label": "A", "skipped_reason": "x", "time_taken_ms": 1}
    assert api.post(f"/annotate/{aid}", json=both, headers=headers).status_code == 422
    bad_code = {"label": "R", "reason_codes": ["vibes"], "time_taken_ms": 1}
    assert api.post(f"/annotate/{aid}", json=bad_code, headers=headers).status_code == 422


def test_only_annotators_reach_annotate_and_only_their_own_items(api):
    seeded = asyncio.run(_seed(1))
    other = asyncio.run(_seed(1))
    api.post("/auth/register", json={"email": "cust.ann@example.com", "full_name": "C", "password": PASSWORD})
    cust = _login(api, "cust.ann@example.com")
    assert api.get("/annotate/next", headers=cust).status_code == 403
    assert api.get("/annotate/next").status_code == 401
    headers = _login(api, seeded["email"])
    resp = api.post(f"/annotate/{other['assignments'][0]}", json={"label": "A", "time_taken_ms": 1}, headers=headers)
    assert resp.status_code == 404
    # Annotator accounts cannot open tickets, queues or admin data.
    assert api.get("/tickets", headers=headers).status_code == 403
    assert api.post("/tickets", data={"subject": "s", "description": "d"}, headers=headers).status_code == 403
    assert api.get("/users", headers=headers).status_code == 403
    assert api.get("/analytics/summary", headers=headers).status_code == 403
