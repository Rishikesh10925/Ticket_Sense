"""GET /tickets/{id}/draft: the structured draft, its evidence and claim scores for the
reviewer workbench; withheld in the escalation lane; never visible to customers."""

import asyncio

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import settings
from app.models import Department
from test_confidence_gate import _admin_token, _department_id_sync, _make_engineer_sync, _register_and_login


def _engineer_token(api, email: str, department_id: str) -> str:
    _make_engineer_sync(email, department_id)
    return api.post("/auth/login", data={"username": email, "password": "password123"}).json()["access_token"]


def _vpn_ticket(api, customer_token: str) -> str:
    resp = api.post(
        "/tickets",
        data={
            "subject": "VPN not connecting from home",
            "description": "My VPN client hangs on connecting and never gets in, need this fixed today",
        },
        headers={"Authorization": f"Bearer {customer_token}"},
    )
    return resp.json()["id"]


def test_engineer_sees_cited_steps_evidence_and_claim_support(api):
    networking_id = _department_id_sync("Networking")
    engineer = _engineer_token(api, "draft_eng@example.com", networking_id)
    ticket_id = _vpn_ticket(api, _register_and_login(api, "draft_customer@example.com"))

    resp = api.get(f"/tickets/{ticket_id}/draft", headers={"Authorization": f"Bearer {engineer}"})
    assert resp.status_code == 200
    draft = resp.json()

    assert draft["shown"] is True and draft["lane"] == "draft"
    assert draft["steps"] and all(step["citations"] for step in draft["steps"])
    cited = {n for step in draft["steps"] for n in step["citations"]}
    assert cited <= {p["n"] for p in draft["evidence"]}
    assert draft["evidence"][0]["title"] == "VPN client hangs while connecting"
    assert draft["claims"] and all(c["support"] is not None for c in draft["claims"])
    assert draft["groundedness"] is not None
    assert len(draft["weakest"]) <= 3
    assert draft["prompt_version"] == "draft-v1"


def test_customer_cannot_read_the_draft(api):
    _department_id_sync("Networking")
    customer = _register_and_login(api, "draft_customer2@example.com")
    ticket_id = _vpn_ticket(api, customer)

    resp = api.get(f"/tickets/{ticket_id}/draft", headers={"Authorization": f"Bearer {customer}"})
    assert resp.status_code == 403


def test_escalation_lane_withholds_the_draft(api):
    # A Networking department with no articles: nothing to cite, so the draft cannot
    # answer and the ticket escalates. The reviewer gets no steps and no claims.
    async def _bare_department() -> str:
        engine = create_async_engine(settings.database_url)
        async with async_sessionmaker(engine, expire_on_commit=False)() as db:
            dept = Department(name="Networking")
            db.add(dept)
            await db.commit()
            dept_id = str(dept.id)
        await engine.dispose()
        return dept_id

    asyncio.run(_bare_department())
    # Escalated tickets are gated behind admin approval, so read them as the admin.
    admin = _admin_token(api, "draft_admin3@example.com")
    ticket_id = _vpn_ticket(api, _register_and_login(api, "draft_customer3@example.com"))

    ticket = api.get(f"/tickets/{ticket_id}", headers={"Authorization": f"Bearer {admin}"}).json()
    assert ticket["status"] == "escalated"
    draft = api.get(f"/tickets/{ticket_id}/draft", headers={"Authorization": f"Bearer {admin}"}).json()
    assert draft["shown"] is False and draft["lane"] == "escalate"
    assert draft["steps"] == [] and draft["claims"] == [] and draft["groundedness"] is None
    assert draft["missing_information"]

    escalation = api.get(f"/tickets/{ticket_id}/escalation", headers={"Authorization": f"Bearer {admin}"}).json()
    assert escalation["reason"] == "The evidence does not answer this ticket"


def test_no_draft_yet_is_404(api):
    # No departments at all: the ticket cannot be routed, so it is never drafted.
    admin = _admin_token(api, "draft_admin@example.com")
    ticket_id = _vpn_ticket(api, _register_and_login(api, "draft_customer4@example.com"))

    resp = api.get(f"/tickets/{ticket_id}/draft", headers={"Authorization": f"Bearer {admin}"})
    assert resp.status_code == 404


def test_a_drafted_ticket_stores_its_signal_vector(api):
    from sqlalchemy import text

    _department_id_sync("Networking")
    ticket_id = _vpn_ticket(api, _register_and_login(api, "signals_customer@example.com"))

    async def _vector():
        engine = create_async_engine(settings.database_url)
        async with engine.connect() as conn:
            row = (await conn.execute(text(
                "SELECT s.feature_version, s.features FROM signal_vectors s JOIN drafts d ON d.id = s.draft_id "
                "WHERE d.ticket_id = :t"), {"t": ticket_id})).one()
        await engine.dispose()
        return row

    version, features = asyncio.run(_vector())
    assert version == "features-v1"
    assert features["ret_top1_fused"] is not None and features["rt_dept_max_prob"] is not None
    assert features["gr_n_steps"] >= 1
