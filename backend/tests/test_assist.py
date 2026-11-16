"""Browser extension API: answer in the fast and assisted lanes, complaint portal
otherwise, portal registry for admins, and the demo portal pages."""

import asyncio
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import settings
from app.core.security import hash_password
from app.models import ComplaintPortal, Department, Ticket, User
from app.routers.demo_portal import DEMO_FIELD_MAP, DEMO_REFERENCE_SELECTOR

PASSWORD = "password123"


def _run(coro):
    return asyncio.run(coro)


async def _with_db(fn):
    engine = create_async_engine(settings.database_url)
    session = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with session() as db:
            result = await fn(db)
            await db.commit()
            return result
    finally:
        await engine.dispose()


def _seed(portals: bool = True) -> dict:
    async def go(db):
        net = Department(name="Networking")
        db.add(net)
        await db.flush()
        suffix = uuid.uuid4().hex[:8]
        users = {
            "owner": User(email=f"owner.{suffix}@example.com", full_name="Asha Owner", role="end_user"),
            "other": User(email=f"other.{suffix}@example.com", full_name="Other", role="end_user"),
            "engineer": User(email=f"eng.{suffix}@example.com", full_name="Eng", role="department_engineer",
                             department_id=net.id),
            "admin": User(email=f"admin.{suffix}@example.com", full_name="Admin", role="admin"),
        }
        for u in users.values():
            u.hashed_password = hash_password(PASSWORD)
        db.add_all(users.values())
        await db.flush()
        if portals:
            db.add_all([
                ComplaintPortal(department_id=net.id, name="Networking complaints",
                                url="http://localhost:8000/demo-portal/networking",
                                field_map=DEMO_FIELD_MAP, reference_selector=DEMO_REFERENCE_SELECTOR),
                ComplaintPortal(department_id=None, name="General complaints",
                                url="http://localhost:8000/demo-portal/general", field_map=DEMO_FIELD_MAP),
            ])
        return {"department_id": net.id, "emails": {k: u.email for k, u in users.items()},
                "owner_id": users["owner"].id}

    return _run(_with_db(go))


def _ticket(seed: dict, **fields) -> uuid.UUID:
    async def go(db):
        ticket = Ticket(submitted_by=seed["owner_id"], subject="VPN drops", description="VPN drops every hour",
                        **fields)
        db.add(ticket)
        await db.flush()
        return ticket.id

    return _run(_with_db(go))


def _headers(api, email: str) -> dict:
    token = api.post("/auth/login", data={"username": email, "password": PASSWORD}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_fast_lane_shows_the_answer_without_a_warning(api):
    seed = _seed()
    tid = _ticket(seed, department_id=seed["department_id"], status="drafted", lane="fast",
                  ai_draft_reply="1. Reconnect the VPN client [1]",
                  ai_draft_citations=[{"title": "VPN reconnect guide"}])
    out = api.get(f"/assist/tickets/{tid}", headers=_headers(api, seed["emails"]["owner"])).json()
    assert out["state"] == "answer"
    assert out["answer"] == "1. Reconnect the VPN client [1]"
    assert out["verify"] is False
    assert out["sources"] == [{"title": "VPN reconnect guide"}]
    # The portal is still offered, in case the answer does not help.
    assert out["portal"]["name"] == "Networking complaints"


def test_assisted_lane_shows_the_answer_with_verify(api):
    seed = _seed()
    tid = _ticket(seed, department_id=seed["department_id"], status="drafted", lane="assisted",
                  ai_draft_reply="Try this", ai_draft_citations=[])
    out = api.get(f"/assist/tickets/{tid}", headers=_headers(api, seed["emails"]["owner"])).json()
    assert out["state"] == "answer"
    assert out["verify"] is True
    assert "verify" in out["message"]


def test_escalated_ticket_goes_to_the_department_portal_with_filled_values(api):
    seed = _seed()
    tid = _ticket(seed, department_id=seed["department_id"], status="escalated", lane="escalate",
                  priority="high", ai_draft_reply=None)
    out = api.get(f"/assist/tickets/{tid}", headers=_headers(api, seed["emails"]["owner"])).json()
    assert out["state"] == "portal"
    assert out["answer"] is None
    portal = out["portal"]
    assert portal["url"].endswith("/demo-portal/networking")
    assert portal["field_map"]["subject"] == "#subject"
    assert portal["values"] == {
        "subject": "VPN drops", "description": "VPN drops every hour", "category": "Networking",
        "priority": "high", "name": "Asha Owner", "email": seed["emails"]["owner"],
        "ticket_ref": f"TS-{str(tid)[:8].upper()}",
    }


def test_unrouted_ticket_falls_back_to_the_default_portal(api):
    seed = _seed()
    tid = _ticket(seed, status="escalated", lane="escalate")
    out = api.get(f"/assist/tickets/{tid}", headers=_headers(api, seed["emails"]["owner"])).json()
    assert out["state"] == "portal"
    assert out["portal"]["name"] == "General complaints"
    assert out["portal"]["values"]["category"] == "General"


def test_no_portal_registered_says_so(api):
    seed = _seed(portals=False)
    tid = _ticket(seed, status="escalated", lane="escalate")
    out = api.get(f"/assist/tickets/{tid}", headers=_headers(api, seed["emails"]["owner"])).json()
    assert out["state"] == "portal"
    assert out["portal"] is None
    assert "no complaint portal" in out["message"]


def test_processing_ticket_has_no_answer_or_portal(api):
    seed = _seed()
    tid = _ticket(seed, status="routed", department_id=seed["department_id"])
    out = api.get(f"/assist/tickets/{tid}", headers=_headers(api, seed["emails"]["owner"])).json()
    assert out["state"] == "processing"
    assert out["answer"] is None and out["portal"] is None


def test_only_the_owner_or_an_admin_can_use_a_ticket(api):
    seed = _seed()
    tid = _ticket(seed, department_id=seed["department_id"], status="drafted", lane="fast", ai_draft_reply="x")
    assert api.get(f"/assist/tickets/{tid}", headers=_headers(api, seed["emails"]["other"])).status_code == 403
    assert api.get(f"/assist/tickets/{tid}", headers=_headers(api, seed["emails"]["engineer"])).status_code == 403
    assert api.get(f"/assist/tickets/{tid}", headers=_headers(api, seed["emails"]["admin"])).status_code == 200
    assert api.get(f"/assist/tickets/{tid}").status_code == 401


def test_portal_reference_is_stored_on_the_ticket(api):
    seed = _seed()
    tid = _ticket(seed, department_id=seed["department_id"], status="escalated", lane="escalate")
    headers = _headers(api, seed["emails"]["owner"])
    portal_id = api.get(f"/assist/tickets/{tid}", headers=headers).json()["portal"]["id"]
    resp = api.post(f"/assist/tickets/{tid}/portal-reference", json={"reference": "NET-123456",
                                                                      "portal_id": portal_id}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["portal_reference"] == "NET-123456"
    assert resp.json()["portal_submitted_at"] is not None
    bad = api.post(f"/assist/tickets/{tid}/portal-reference", json={"reference": "<script>"}, headers=headers)
    assert bad.status_code == 422
    other = _headers(api, seed["emails"]["other"])
    assert api.post(f"/assist/tickets/{tid}/portal-reference", json={"reference": "X1"},
                    headers=other).status_code == 403


def test_admin_manages_portals(api):
    seed = _seed(portals=False)
    admin = _headers(api, seed["emails"]["admin"])
    body = {"department_id": str(seed["department_id"]), "name": "Net desk", "url": "https://example.org/complain",
            "field_map": {"subject": "#s", "description": "#d"}, "reference_selector": ".ref"}
    created = api.put("/portals", json=body, headers=admin)
    assert created.status_code == 200
    assert created.json()["department_name"] == "Networking"
    # PUT again replaces, it does not add a second portal for the department.
    body["name"] = "Network desk"
    assert api.put("/portals", json=body, headers=admin).json()["name"] == "Network desk"
    listed = api.get("/portals", headers=admin).json()
    assert [p["name"] for p in listed] == ["Network desk"]

    assert api.put("/portals", json={**body, "url": "javascript:alert(1)"}, headers=admin).status_code == 422
    assert api.put("/portals", json={**body, "field_map": {"password": "#p"}}, headers=admin).status_code == 422
    owner = _headers(api, seed["emails"]["owner"])
    assert api.get("/portals", headers=owner).status_code == 403
    assert api.put("/portals", json=body, headers=owner).status_code == 403

    assert api.delete(f"/portals/{listed[0]['id']}", headers=admin).status_code == 204

    async def count(db):
        return len(list(await db.scalars(select(ComplaintPortal))))

    assert _run(_with_db(count)) == 0


def test_demo_portal_form_and_confirmation(api):
    form = api.get("/demo-portal/networking")
    assert form.status_code == 200
    for selector in DEMO_FIELD_MAP.values():
        assert f'id={selector[1:]} ' in form.text or f'id={selector[1:]}>' in form.text
    done = api.post("/demo-portal/networking", data={
        "name": "Asha", "email": "a@example.com", "subject": "<b>VPN</b>", "description": "drops",
        "category": "Networking", "priority": "high", "ticket_ref": "TS-1"})
    assert done.status_code == 200
    assert "data-complaint-reference>NET-" in done.text
    assert "<b>VPN</b>" not in done.text  # user input is escaped
