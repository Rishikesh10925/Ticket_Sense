import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import settings
from app.core.security import hash_password
from app.models import Department, User


def _register_and_login(api, email: str) -> str:
    api.post("/auth/register", json={"email": email, "full_name": "Test User", "password": "password123"})
    resp = api.post("/auth/login", data={"username": email, "password": "password123"})
    return resp.json()["access_token"]


def _department_id_sync(name: str) -> str:
    async def _get():
        engine = create_async_engine(settings.database_url)
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        async with session_factory() as db:
            dept = await db.scalar(select(Department).where(Department.name == name))
            if dept is None:
                dept = Department(name=name)
                db.add(dept)
                await db.commit()
                await db.refresh(dept)
            result = str(dept.id)
        await engine.dispose()
        return result

    return asyncio.run(_get())


def _make_engineer_sync(email: str, department_id: str) -> None:
    async def _create():
        engine = create_async_engine(settings.database_url)
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        async with session_factory() as db:
            db.add(
                User(
                    email=email,
                    full_name="Engineer",
                    role="department_engineer",
                    department_id=department_id,
                    hashed_password=hash_password("password123"),
                )
            )
            await db.commit()
        await engine.dispose()

    asyncio.run(_create())


def _create_admin_sync(email: str) -> None:
    async def _create():
        engine = create_async_engine(settings.database_url)
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        async with session_factory() as db:
            db.add(
                User(
                    email=email,
                    full_name="Admin",
                    role="admin",
                    hashed_password=hash_password("password123"),
                )
            )
            await db.commit()
        await engine.dispose()

    asyncio.run(_create())


def _admin_token(api, email: str) -> str:
    _create_admin_sync(email)
    return api.post("/auth/login", data={"username": email, "password": "password123"}).json()["access_token"]


def test_high_confidence_ticket_reaches_drafted(api):
    networking_id = _department_id_sync("Networking")
    _make_engineer_sync("gate_eng_high@example.com", networking_id)
    engineer_token = api.post(
        "/auth/login", data={"username": "gate_eng_high@example.com", "password": "password123"}
    ).json()["access_token"]

    token = _register_and_login(api, "gate_user_high@example.com")
    resp = api.post(
        "/tickets",
        data={
            "subject": "VPN not connecting from home",
            "description": "My VPN client hangs on connecting and never gets in, need this fixed today",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    ticket_id = resp.json()["id"]

    ticket = api.get(f"/tickets/{ticket_id}", headers={"Authorization": f"Bearer {engineer_token}"}).json()
    assert ticket["status"] == "drafted"
    assert ticket["ai_draft_reply"]


def test_low_confidence_ticket_is_escalated_with_no_draft(api):
    networking_id = _department_id_sync("Networking")
    admin_token = _admin_token(api, "gate_admin_low@example.com")

    # Force the gate to fail regardless of the actual score, so this test doesn't
    # depend on the model's exact output — an unreachably high bar.
    api.patch(
        f"/departments/{networking_id}/threshold",
        json={"confidence_threshold": 1.0},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    token = _register_and_login(api, "gate_user_low@example.com")
    resp = api.post(
        "/tickets",
        data={
            "subject": "VPN not connecting from home",
            "description": "My VPN client hangs on connecting and never gets in, need this fixed today",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    ticket_id = resp.json()["id"]

    ticket = api.get(f"/tickets/{ticket_id}", headers={"Authorization": f"Bearer {admin_token}"}).json()
    assert ticket["status"] == "escalated"
    assert ticket["ai_draft_reply"] is None
    assert ticket["ai_draft_citations"] is None
    assert ticket["confidence_score"] is not None
    assert ticket["confidence_threshold"] == 1.0

    escalation = api.get(
        f"/tickets/{ticket_id}/escalation", headers={"Authorization": f"Bearer {admin_token}"}
    ).json()
    assert "threshold" in escalation["reason"].lower()
    assert escalation["confidence_score"] == ticket["confidence_score"]


def test_escalation_endpoint_404_when_not_escalated(api):
    networking_id = _department_id_sync("Networking")
    admin_token = _admin_token(api, "gate_admin_404@example.com")

    token = _register_and_login(api, "gate_user_404@example.com")
    resp = api.post(
        "/tickets",
        data={"subject": "VPN not connecting", "description": "VPN client hangs on connecting today"},
        headers={"Authorization": f"Bearer {token}"},
    )
    ticket_id = resp.json()["id"]

    resp = api.get(f"/tickets/{ticket_id}/escalation", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 404


def test_escalation_endpoint_requires_reviewer_role(api):
    networking_id = _department_id_sync("Networking")
    admin_token = _admin_token(api, "gate_admin_role@example.com")
    api.patch(
        f"/departments/{networking_id}/threshold",
        json={"confidence_threshold": 1.0},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    token = _register_and_login(api, "gate_user_role@example.com")
    resp = api.post(
        "/tickets",
        data={"subject": "VPN not connecting", "description": "VPN client hangs on connecting today"},
        headers={"Authorization": f"Bearer {token}"},
    )
    ticket_id = resp.json()["id"]

    resp = api.get(f"/tickets/{ticket_id}/escalation", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403


def test_feedback_accept_transitions_to_reviewed(api):
    networking_id = _department_id_sync("Networking")
    _make_engineer_sync("gate_eng_accept@example.com", networking_id)
    engineer_token = api.post(
        "/auth/login", data={"username": "gate_eng_accept@example.com", "password": "password123"}
    ).json()["access_token"]

    token = _register_and_login(api, "gate_user_accept@example.com")
    resp = api.post(
        "/tickets",
        data={
            "subject": "VPN not connecting from home",
            "description": "My VPN client hangs on connecting and never gets in, need this fixed today",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    ticket_id = resp.json()["id"]

    resp = api.post(
        f"/tickets/{ticket_id}/feedback",
        json={"action": "accept"},
        headers={"Authorization": f"Bearer {engineer_token}"},
    )
    assert resp.status_code == 201
    assert resp.json()["status"] == "reviewed"


def test_feedback_edit_requires_edited_reply(api):
    networking_id = _department_id_sync("Networking")
    _make_engineer_sync("gate_eng_edit@example.com", networking_id)
    engineer_token = api.post(
        "/auth/login", data={"username": "gate_eng_edit@example.com", "password": "password123"}
    ).json()["access_token"]

    token = _register_and_login(api, "gate_user_edit@example.com")
    resp = api.post(
        "/tickets",
        data={
            "subject": "VPN not connecting from home",
            "description": "My VPN client hangs on connecting and never gets in, need this fixed today",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    ticket_id = resp.json()["id"]

    resp = api.post(
        f"/tickets/{ticket_id}/feedback",
        json={"action": "edit"},
        headers={"Authorization": f"Bearer {engineer_token}"},
    )
    assert resp.status_code == 422

    resp = api.post(
        f"/tickets/{ticket_id}/feedback",
        json={"action": "edit", "edited_reply": "A corrected reply."},
        headers={"Authorization": f"Bearer {engineer_token}"},
    )
    assert resp.status_code == 201
    assert resp.json()["status"] == "reviewed"
    # The AI's original draft is untouched — the edit lives on the feedback row, not
    # overwriting ai_draft_reply (see app/routers/tickets.py's submit_ticket_feedback).
    assert resp.json()["ai_draft_reply"] != "A corrected reply."


def test_feedback_escalate_after_draft_creates_escalation(api):
    networking_id = _department_id_sync("Networking")
    _make_engineer_sync("gate_eng_escalate@example.com", networking_id)
    engineer_token = api.post(
        "/auth/login", data={"username": "gate_eng_escalate@example.com", "password": "password123"}
    ).json()["access_token"]

    token = _register_and_login(api, "gate_user_escalate@example.com")
    resp = api.post(
        "/tickets",
        data={
            "subject": "VPN not connecting from home",
            "description": "My VPN client hangs on connecting and never gets in, need this fixed today",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    ticket_id = resp.json()["id"]

    resp = api.post(
        f"/tickets/{ticket_id}/feedback",
        json={"action": "escalate"},
        headers={"Authorization": f"Bearer {engineer_token}"},
    )
    assert resp.status_code == 201
    assert resp.json()["status"] == "escalated"

    escalation = api.get(
        f"/tickets/{ticket_id}/escalation", headers={"Authorization": f"Bearer {engineer_token}"}
    ).json()
    assert "engineer" in escalation["reason"].lower()


def test_feedback_requires_drafted_status(api):
    networking_id = _department_id_sync("Networking")
    _make_engineer_sync("gate_eng_conflict@example.com", networking_id)
    engineer_token = api.post(
        "/auth/login", data={"username": "gate_eng_conflict@example.com", "password": "password123"}
    ).json()["access_token"]

    token = _register_and_login(api, "gate_user_conflict@example.com")
    resp = api.post(
        "/tickets",
        data={
            "subject": "VPN not connecting from home",
            "description": "My VPN client hangs on connecting and never gets in, need this fixed today",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    ticket_id = resp.json()["id"]

    # Accept once — status becomes "reviewed".
    api.post(
        f"/tickets/{ticket_id}/feedback",
        json={"action": "accept"},
        headers={"Authorization": f"Bearer {engineer_token}"},
    )
    # A second review action on the same ticket should be rejected.
    resp = api.post(
        f"/tickets/{ticket_id}/feedback",
        json={"action": "accept"},
        headers={"Authorization": f"Bearer {engineer_token}"},
    )
    assert resp.status_code == 409


def test_feedback_requires_reviewer_role(api):
    networking_id = _department_id_sync("Networking")
    token = _register_and_login(api, "gate_user_norole@example.com")
    resp = api.post(
        "/tickets",
        data={
            "subject": "VPN not connecting from home",
            "description": "My VPN client hangs on connecting and never gets in, need this fixed today",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    ticket_id = resp.json()["id"]

    resp = api.post(
        f"/tickets/{ticket_id}/feedback",
        json={"action": "accept"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403
