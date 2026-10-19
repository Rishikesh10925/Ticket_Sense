"""Role matrix (Blueprint V2 §16: "Role matrix test suite"; Roadmap Week 3).

Every protected route is called as anonymous, end user, department engineer and admin.
An allowed role must not get 401/403; every other role must get 401 (anonymous) or 403.
Ticket routes are also checked per department: an engineer in another department, or a
different end user, must not read someone else's ticket.
"""

import asyncio
import uuid

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import settings
from app.core.security import hash_password
from app.models import Department, Ticket, User

PASSWORD = "password123"
ROLES = ("anonymous", "end_user", "department_engineer", "admin")
ANY_SIGNED_IN = {"end_user", "department_engineer", "admin"}
STAFF = {"department_engineer", "admin"}
ADMIN = {"admin"}
NIL = "00000000-0000-0000-0000-000000000000"

# (method, path, json body, roles allowed)
MATRIX = [
    ("GET", "/auth/me", None, ANY_SIGNED_IN),
    ("GET", "/departments", None, ANY_SIGNED_IN),
    ("PATCH", f"/departments/{NIL}/threshold", {"confidence_threshold": 0.5}, ADMIN),
    ("GET", "/users", None, ADMIN),
    ("POST", "/users", {"email": "x@example.com", "full_name": "X", "password": PASSWORD, "role": "admin"}, ADMIN),
    ("PATCH", f"/users/{NIL}", {"full_name": "Y"}, ADMIN),
    ("GET", "/knowledge-base", None, ADMIN),
    ("POST", "/knowledge-base", {"department_id": NIL, "title": "t", "content": "c"}, ADMIN),
    ("GET", "/escalations/pending", None, ADMIN),
    ("POST", f"/escalations/{NIL}/approve", {}, ADMIN),
    ("POST", f"/escalations/{NIL}/reject", {}, ADMIN),
    ("GET", "/analytics/summary", None, STAFF),
    ("GET", "/analytics/confidence-model", None, ADMIN),
    ("GET", "/messages/contacts", None, STAFF),
    ("GET", f"/messages/thread/{NIL}", None, STAFF),
    ("POST", "/messages", {"recipient_id": NIL, "body": "hi"}, STAFF),
    ("GET", "/tickets", None, ANY_SIGNED_IN),
]


def _run(coro):
    return asyncio.run(coro)


async def _seed() -> dict:
    engine = create_async_engine(settings.database_url)
    session = async_sessionmaker(engine, expire_on_commit=False)
    async with session() as db:
        networking, sap = Department(name="Networking"), Department(name="SAP")
        db.add_all([networking, sap])
        await db.flush()
        suffix = uuid.uuid4().hex[:8]
        users = {
            "end_user": User(email=f"owner.{suffix}@example.com", full_name="Owner", role="end_user"),
            "other_end_user": User(email=f"other.{suffix}@example.com", full_name="Other", role="end_user"),
            "department_engineer": User(
                email=f"neteng.{suffix}@example.com", full_name="Net Eng", role="department_engineer",
                department_id=networking.id,
            ),
            "other_engineer": User(
                email=f"sapeng.{suffix}@example.com", full_name="SAP Eng", role="department_engineer",
                department_id=sap.id,
            ),
            "admin": User(email=f"admin.{suffix}@example.com", full_name="Admin", role="admin"),
        }
        for u in users.values():
            u.hashed_password = hash_password(PASSWORD)
        db.add_all(users.values())
        await db.flush()
        # Routed and drafted, so it sits in the Networking queue for engineers.
        ticket = Ticket(
            submitted_by=users["end_user"].id, department_id=networking.id, subject="VPN down",
            description="VPN hangs", status="drafted",
        )
        db.add(ticket)
        await db.commit()
        result = {"emails": {k: u.email for k, u in users.items()}, "ticket_id": str(ticket.id)}
    await engine.dispose()
    return result


@pytest.fixture
def seeded(api):
    data = _run(_seed())
    tokens = {}
    for role, email in data["emails"].items():
        resp = api.post("/auth/login", data={"username": email, "password": PASSWORD})
        assert resp.status_code == 200, (role, resp.text)
        tokens[role] = resp.json()["access_token"]
    return {"tokens": tokens, "ticket_id": data["ticket_id"]}


def _call(api, method, path, body, token):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    return api.request(method, path, json=body, headers=headers)


@pytest.mark.parametrize(("method", "path", "body", "allowed"), MATRIX, ids=[f"{m} {p}" for m, p, _, _ in MATRIX])
def test_role_matrix(api, seeded, method, path, body, allowed):
    for role in ROLES:
        token = None if role == "anonymous" else seeded["tokens"][role]
        status = _call(api, method, path, body, token).status_code
        if role in allowed:
            assert status not in (401, 403), f"{role} should reach {method} {path}, got {status}"
        elif role == "anonymous":
            assert status == 401, f"anonymous should get 401 on {method} {path}, got {status}"
        else:
            assert status == 403, f"{role} should get 403 on {method} {path}, got {status}"


def test_ticket_visibility_is_scoped_by_owner_and_department(api, seeded):
    tid, tokens = seeded["ticket_id"], seeded["tokens"]
    path = f"/tickets/{tid}"
    for role in ("end_user", "department_engineer", "admin"):
        assert _call(api, "GET", path, None, tokens[role]).status_code == 200, role
    for role in ("other_end_user", "other_engineer"):
        assert _call(api, "GET", path, None, tokens[role]).status_code in (403, 404), role
    assert _call(api, "GET", path, None, None).status_code == 401


def test_end_users_never_see_evidence_even_for_their_own_ticket(api, seeded):
    tid, tokens = seeded["ticket_id"], seeded["tokens"]
    assert _call(api, "GET", f"/tickets/{tid}/evidence", None, tokens["end_user"]).status_code == 403
    assert _call(api, "GET", f"/tickets/{tid}/evidence", None, tokens["other_engineer"]).status_code in (403, 404)
    assert _call(api, "GET", f"/tickets/{tid}/evidence", None, tokens["department_engineer"]).status_code == 200


def test_end_users_cannot_review_and_other_departments_cannot_either(api, seeded):
    tid, tokens = seeded["ticket_id"], seeded["tokens"]
    body = {"action": "accept"}
    assert _call(api, "POST", f"/tickets/{tid}/feedback", body, tokens["end_user"]).status_code == 403
    assert _call(api, "POST", f"/tickets/{tid}/feedback", body, tokens["other_engineer"]).status_code in (403, 404)


def test_end_user_ticket_list_contains_only_their_own(api, seeded):
    tokens, tid = seeded["tokens"], seeded["ticket_id"]
    own = _call(api, "GET", "/tickets", None, tokens["end_user"]).json()
    other = _call(api, "GET", "/tickets", None, tokens["other_end_user"]).json()
    sap = _call(api, "GET", "/tickets", None, tokens["other_engineer"]).json()
    assert [t["id"] for t in own] == [tid]
    assert other == [] and all(t["id"] != tid for t in sap)
