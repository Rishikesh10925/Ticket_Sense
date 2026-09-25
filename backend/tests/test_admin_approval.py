import asyncio
import time

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import settings
from app.core.security import hash_password
from app.models import Department, Feedback, Ticket, User


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


def _make_engineer_sync(email: str, department_id: str) -> str:
    async def _create():
        engine = create_async_engine(settings.database_url)
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        async with session_factory() as db:
            user = User(
                email=email,
                full_name="Engineer",
                role="department_engineer",
                department_id=department_id,
                hashed_password=hash_password("password123"),
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
            result = str(user.id)
        await engine.dispose()
        return result

    return asyncio.run(_create())


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


def _mark_ticket_reviewed_with_no_feedback_sync(ticket_id: str) -> None:
    """Simulates what pipeline.py's auto-resolution actually does: a `drafted`
    ticket moves straight to `reviewed` with zero Feedback rows. Used here instead of
    forcing a real score >= 0.85 through the model, which isn't deterministically
    controllable through the public API."""

    async def _update():
        engine = create_async_engine(settings.database_url)
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        async with session_factory() as db:
            ticket = await db.get(Ticket, ticket_id)
            ticket.status = "reviewed"
            await db.commit()
        await engine.dispose()

    asyncio.run(_update())


def _wait_for_status(api, token: str, ticket_id: str, target_statuses: tuple[str, ...], tries: int = 15) -> dict:
    """The pipeline runs as a genuine background task, not synchronously with the
    POST that starts it -- normally fast enough that an immediate GET already sees
    the final status, but the very first classification in a freshly-started test
    process pays a one-time model-loading cost that can outlast that. Polls briefly
    rather than assuming either timing."""
    ticket = {}
    for _ in range(tries):
        ticket = api.get(f"/tickets/{ticket_id}", headers={"Authorization": f"Bearer {token}"}).json()
        if ticket.get("status") in target_statuses:
            return ticket
        time.sleep(1)
    return ticket


def _submit_and_force_escalation(api, customer_token: str, admin_token: str, department_id: str, subject: str, description: str) -> str:
    """Forces a ticket to escalate deterministically (threshold=1.0, same technique
    test_confidence_gate.py already uses), then restores a normal threshold so it
    doesn't affect other tickets in the same test."""
    api.patch(
        f"/departments/{department_id}/threshold",
        json={"confidence_threshold": 1.0},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    resp = api.post(
        "/tickets",
        data={"subject": subject, "description": description},
        headers={"Authorization": f"Bearer {customer_token}"},
    )
    ticket_id = resp.json()["id"]
    _wait_for_status(api, admin_token, ticket_id, ("escalated",))
    api.patch(
        f"/departments/{department_id}/threshold",
        json={"confidence_threshold": 0.5},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    return ticket_id


def test_auto_resolved_ticket_shows_final_response_to_customer(api):
    """Simulates pipeline.py's auto-resolution (score >= the customer-facing 0.85
    bar skips the engineer entirely) by directly moving a real drafted ticket to
    `reviewed` with no Feedback row -- forcing an actual >=0.85 score isn't
    deterministically possible through the public API, but this exercises the exact
    downstream behavior that matters: _final_responses_for treats a `reviewed`
    ticket with zero feedback as "the draft itself was the response"."""
    _department_id_sync("Networking")  # must exist before the classifier can route into it
    customer_token = _register_and_login(api, "approval_customer_auto@example.com")
    resp = api.post(
        "/tickets",
        data={"subject": "VPN not connecting", "description": "VPN client hangs on connecting"},
        headers={"Authorization": f"Bearer {customer_token}"},
    )
    ticket_id = resp.json()["id"]

    admin_token = _admin_token(api, "approval_admin_auto@example.com")
    ticket = _wait_for_status(api, admin_token, ticket_id, ("drafted", "escalated"))
    assert ticket["status"] == "drafted"
    original_draft = ticket["ai_draft_reply"]
    assert original_draft

    _mark_ticket_reviewed_with_no_feedback_sync(ticket_id)

    customer_view = api.get(f"/tickets/{ticket_id}", headers={"Authorization": f"Bearer {customer_token}"}).json()
    assert customer_view["status"] == "reviewed"
    assert customer_view["final_response"] == original_draft
    assert customer_view["ai_draft_reply"] is None  # still hidden -- final_response is the customer-facing copy


def test_escalated_ticket_not_visible_to_unassigned_engineer_in_same_department(api):
    dept_id = _department_id_sync("Networking")
    admin_token = _admin_token(api, "approval_admin1@example.com")
    _make_engineer_sync("approval_eng_unassigned@example.com", dept_id)
    unassigned_token = api.post(
        "/auth/login", data={"username": "approval_eng_unassigned@example.com", "password": "password123"}
    ).json()["access_token"]
    customer_token = _register_and_login(api, "approval_customer1@example.com")

    ticket_id = _submit_and_force_escalation(
        api, customer_token, admin_token, dept_id, "VPN not connecting", "VPN client hangs on connecting"
    )

    # Not in this engineer's queue at all -- escalated tickets are gated behind
    # admin approval, not visible department-wide.
    queue = api.get("/tickets", headers={"Authorization": f"Bearer {unassigned_token}"}).json()
    assert ticket_id not in [t["id"] for t in queue]

    # And a direct fetch is a 403, same as any other out-of-scope ticket.
    resp = api.get(f"/tickets/{ticket_id}", headers={"Authorization": f"Bearer {unassigned_token}"})
    assert resp.status_code == 403


def test_admin_sees_the_escalation_in_the_pending_queue(api):
    dept_id = _department_id_sync("Networking")
    admin_token = _admin_token(api, "approval_admin2@example.com")
    customer_token = _register_and_login(api, "approval_customer2@example.com")

    ticket_id = _submit_and_force_escalation(
        api, customer_token, admin_token, dept_id, "Wifi keeps dropping", "Wifi drops every few minutes"
    )

    pending = api.get("/escalations/pending", headers={"Authorization": f"Bearer {admin_token}"}).json()
    assert ticket_id in [row["ticket_id"] for row in pending]


def test_full_approve_then_resolve_flow_reflects_in_customer_portal(api):
    dept_id = _department_id_sync("Networking")
    admin_token = _admin_token(api, "approval_admin3@example.com")
    engineer_id = _make_engineer_sync("approval_eng_assigned@example.com", dept_id)
    engineer_token = api.post(
        "/auth/login", data={"username": "approval_eng_assigned@example.com", "password": "password123"}
    ).json()["access_token"]
    customer_token = _register_and_login(api, "approval_customer3@example.com")

    ticket_id = _submit_and_force_escalation(
        api, customer_token, admin_token, dept_id, "Slow internet at desk", "My connection has been slow all day"
    )

    pending = api.get("/escalations/pending", headers={"Authorization": f"Bearer {admin_token}"}).json()
    escalation_id = next(row["id"] for row in pending if row["ticket_id"] == ticket_id)

    approve_resp = api.post(
        f"/escalations/{escalation_id}/approve",
        json={"engineer_id": engineer_id},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert approve_resp.status_code == 200
    assert approve_resp.json()["escalated_to"] == engineer_id
    assert approve_resp.json()["admin_decision"] == "approved"

    # Now it shows up in the assigned engineer's queue.
    queue = api.get("/tickets", headers={"Authorization": f"Bearer {engineer_token}"}).json()
    assert ticket_id in [t["id"] for t in queue]

    resolve_resp = api.post(
        f"/tickets/{ticket_id}/resolve-escalation",
        json={"response_text": "Please restart your router and it should clear up."},
        headers={"Authorization": f"Bearer {engineer_token}"},
    )
    assert resolve_resp.status_code == 201
    assert resolve_resp.json()["status"] == "reviewed"

    # The customer now sees the actual response, and nothing else AI-internal.
    ticket = api.get(f"/tickets/{ticket_id}", headers={"Authorization": f"Bearer {customer_token}"}).json()
    assert ticket["final_response"] == "Please restart your router and it should clear up."
    assert ticket["confidence_score"] is None
    assert ticket["ai_draft_reply"] is None


def test_admin_can_reject_an_escalation_and_close_it_without_an_engineer(api):
    dept_id = _department_id_sync("Networking")
    admin_token = _admin_token(api, "approval_admin4@example.com")
    customer_token = _register_and_login(api, "approval_customer4@example.com")

    ticket_id = _submit_and_force_escalation(
        api, customer_token, admin_token, dept_id, "VPN not connecting", "VPN client hangs on connecting"
    )
    pending = api.get("/escalations/pending", headers={"Authorization": f"Bearer {admin_token}"}).json()
    escalation_id = next(row["id"] for row in pending if row["ticket_id"] == ticket_id)

    reject_resp = api.post(
        f"/escalations/{escalation_id}/reject",
        json={"note": "Duplicate of an earlier ticket"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert reject_resp.status_code == 200
    assert reject_resp.json()["admin_decision"] == "rejected"

    ticket = api.get(f"/tickets/{ticket_id}", headers={"Authorization": f"Bearer {admin_token}"}).json()
    assert ticket["status"] == "closed"

    # Already-decided escalations can't be decided again.
    second_attempt = api.post(
        f"/escalations/{escalation_id}/reject",
        json={"note": "trying again"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert second_attempt.status_code == 409


def test_only_admin_can_use_the_approval_endpoints(api):
    customer_token = _register_and_login(api, "approval_customer5@example.com")
    resp = api.get("/escalations/pending", headers={"Authorization": f"Bearer {customer_token}"})
    assert resp.status_code == 403


def test_doubt_sends_a_drafted_ticket_back_to_the_pending_admin_queue(api):
    dept_id = _department_id_sync("Networking")
    admin_token = _admin_token(api, "approval_admin6@example.com")
    _make_engineer_sync("approval_eng_doubt@example.com", dept_id)
    engineer_token = api.post(
        "/auth/login", data={"username": "approval_eng_doubt@example.com", "password": "password123"}
    ).json()["access_token"]
    customer_token = _register_and_login(api, "approval_customer6@example.com")

    resp = api.post(
        "/tickets",
        data={"subject": "VPN not connecting", "description": "VPN client hangs on connecting"},
        headers={"Authorization": f"Bearer {customer_token}"},
    )
    ticket_id = resp.json()["id"]
    ticket = api.get(f"/tickets/{ticket_id}", headers={"Authorization": f"Bearer {engineer_token}"}).json()
    assert ticket["status"] == "drafted"

    doubt_resp = api.post(
        f"/tickets/{ticket_id}/feedback",
        json={"action": "doubt", "reject_reason": "Not sure this is really a Networking issue"},
        headers={"Authorization": f"Bearer {engineer_token}"},
    )
    assert doubt_resp.status_code == 201
    assert doubt_resp.json()["status"] == "escalated"

    pending = api.get("/escalations/pending", headers={"Authorization": f"Bearer {admin_token}"}).json()
    assert ticket_id in [row["ticket_id"] for row in pending]

    # And it's gone from the engineer's own queue now -- back to admin-gated.
    queue = api.get("/tickets", headers={"Authorization": f"Bearer {engineer_token}"}).json()
    assert ticket_id not in [t["id"] for t in queue]
