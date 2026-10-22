"""User study (Roadmap Week 11): blinding per condition, server-side timing, allowed
actions, KB search and counterbalancing."""

import asyncio
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import settings
from app.core.security import hash_password
from app.models import BenchmarkTicket, Department, Draft, DraftClaim, KnowledgeBase, StudyParticipant, StudyTask, User
from app.services.study import order_for, plan, rank_articles, search_terms

PASSWORD = "password123"
HIDDEN = ("type", "gold", "split", "set", "key", "group", "department", "score", "ticket_id")


async def _seed(conditions_lanes: list[tuple[str, str]]) -> dict:
    engine = create_async_engine(settings.database_url)
    session = async_sessionmaker(engine, expire_on_commit=False)
    async with session() as db:
        suffix = uuid.uuid4().hex[:6]
        user = User(email=f"p.{suffix}@study.local", full_name="Participant", role="participant",
                    hashed_password=hash_password(PASSWORD))
        db.add(user)
        await db.flush()
        participant = StudyParticipant(user_id=user.id, code=f"T{suffix[:4]}", order="manual_first")
        db.add(participant)
        await db.flush()
        task_ids = []
        for i, (condition, lane) in enumerate(conditions_lanes):
            ticket = BenchmarkTicket(
                id=f"S-{suffix}{i}", benchmark_version="test", group_id="G-1", subject=f"VPN issue {i}",
                body="VPN hangs at connecting.", department="Networking", priority="high", type="A",
                gold_articles=["NET-VPN-001"], split="val",
            )
            db.add(ticket)
            await db.flush()
            draft = Draft(
                benchmark_ticket_id=ticket.id, benchmark_version="test", model="qwen2.5:7b-instruct",
                prompt_version="draft-v2", schema_valid=True, can_answer=True,
                steps=[{"text": "Retry from a mobile hotspot.", "citations": [1]}], missing_information=[],
                evidence=[{"n": 1, "article_key": "NET-VPN-001", "title": "VPN client not connecting",
                           "text": "Retry from a mobile hotspot."}],
                raw_text="{}", groundedness=0.9,
            )
            db.add(draft)
            await db.flush()
            db.add(DraftClaim(draft_id=draft.id, step_index=0, claim_index=0, text="Retry from a mobile hotspot.",
                              cited=[1], support=0.42))
            task = StudyTask(participant_id=participant.id, draft_id=draft.id, benchmark_ticket_id=ticket.id,
                             ticket_set="A", condition=condition, position=i, lane=lane, score=0.7,
                             reasons=["weak best retrieval match"])
            db.add(task)
            await db.flush()
            task_ids.append(str(task.id))
        department = Department(name=f"Networking-{suffix}")
        db.add(department)
        await db.flush()
        db.add(KnowledgeBase(department_id=department.id, title=f"VPN client not connecting {suffix}",
                             content="Retry from a mobile hotspot.", article_key=f"K-{suffix}"))
        await db.commit()
    await engine.dispose()
    return {"email": user.email, "tasks": task_ids, "suffix": suffix}


async def _task(task_id: str) -> StudyTask:
    engine = create_async_engine(settings.database_url)
    async with async_sessionmaker(engine)() as db:
        task = await db.scalar(select(StudyTask).where(StudyTask.id == uuid.UUID(task_id)))
    await engine.dispose()
    return task


def _login(api, email):
    token = api.post("/auth/login", data={"username": email, "password": PASSWORD}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _keys(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield k
            yield from _keys(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _keys(v)


def test_manual_condition_shows_no_ai(api):
    seeded = asyncio.run(_seed([("manual", "assisted")]))
    item = api.get("/study/next", headers=_login(api, seeded["email"])).json()
    assert item["condition"] == "manual"
    assert item["draft"] is None and item["lane"] is None and item["reasons"] == [] and item["weakest_claims"] == []
    assert not set(_keys(item)) & set(HIDDEN)


def test_workbench_shows_lane_draft_and_weakest_claims(api):
    seeded = asyncio.run(_seed([("workbench", "assisted")]))
    item = api.get("/study/next", headers=_login(api, seeded["email"])).json()
    assert item["lane"] == "assisted" and item["reasons"] == ["weak best retrieval match"]
    assert item["draft"]["steps"][0]["text"] == "Retry from a mobile hotspot."
    assert item["weakest_claims"] == [{"step": 1, "text": "Retry from a mobile hotspot.", "support": 0.42}]
    assert not set(_keys(item)) & set(HIDDEN)


def test_escalated_workbench_task_has_no_draft(api):
    seeded = asyncio.run(_seed([("workbench", "escalate")]))
    headers = _login(api, seeded["email"])
    item = api.get("/study/next", headers=headers).json()
    assert item["lane"] == "escalate" and item["draft"] is None and item["evidence"] == []
    bad = api.post(f"/study/tasks/{item['task_id']}", json={"action": "accept", "final_reply": "x"}, headers=headers)
    assert bad.status_code == 422


def test_submission_is_timed_on_the_server_and_final(api):
    seeded = asyncio.run(_seed([("manual", "assisted"), ("manual", "assisted")]))
    headers = _login(api, seeded["email"])
    first = api.get("/study/next", headers=headers).json()
    assert first["task_id"] == seeded["tasks"][0] and first["progress"] == {"done": 0, "total": 2}
    assert api.post(f"/study/tasks/{first['task_id']}", json={"action": "accept", "final_reply": "x"},
                    headers=headers).status_code == 422  # no draft to accept in the manual condition
    assert api.post(f"/study/tasks/{first['task_id']}", json={"action": "write", "final_reply": "  "},
                    headers=headers).status_code == 422  # empty reply
    ok = api.post(f"/study/tasks/{first['task_id']}", json={"action": "write", "final_reply": "Use a hotspot."},
                  headers=headers)
    assert ok.status_code == 201 and ok.json()["progress"]["done"] == 1
    again = api.post(f"/study/tasks/{first['task_id']}", json={"action": "escalate"}, headers=headers)
    assert again.status_code == 409
    task = asyncio.run(_task(first["task_id"]))
    assert task.action == "write" and task.time_ms is not None and task.time_ms >= 0
    assert api.get("/study/next", headers=headers).json()["task_id"] == seeded["tasks"][1]


def test_kb_search_and_role_restriction(api):
    seeded = asyncio.run(_seed([("manual", "assisted")]))
    headers = _login(api, seeded["email"])
    found = api.get("/study/kb", params={"q": f"vpn connecting {seeded['suffix']}"}, headers=headers).json()
    assert found and found[0]["title"].endswith(seeded["suffix"])
    # A participant can reach nothing else.
    assert api.get("/tickets", headers=headers).status_code == 403
    assert api.get("/annotate/next", headers=headers).status_code == 403


def test_counterbalancing_and_plan():
    assert [order_for(i) for i in range(4)] == ["manual_first", "workbench_first", "manual_first", "workbench_first"]
    a, b = [f"A{i}" for i in range(20)], [f"B{i}" for i in range(20)]
    p1, p2 = plan("P01", "manual_first", a, b), plan("P02", "workbench_first", a, b)
    assert [c for _, s, c in p1 if s == "A"] == ["manual"] * 20 and [c for _, s, c in p1 if s == "B"] == ["workbench"] * 20
    assert [c for _, s, c in p2 if s == "A"] == ["workbench"] * 20
    assert sorted(t for t, _, _ in p1) == sorted(a + b) and p1 == plan("P01", "manual_first", a, b)
    assert [t for t, _, _ in p1[:20]] != [t for t, _, _ in p2[:20]]  # shuffled per participant


def test_keyword_ranking():
    assert search_terms("VPN is down, help!") == ["vpn", "down", "help"]
    articles = [("K1", "Printer jam", "paper vpn"), ("K2", "VPN not connecting", "client"), ("K3", "Leave", "days")]
    assert [k for k, _, _ in rank_articles(articles, ["vpn"])] == ["K2", "K1"]
