"""Week 8 gate: versioned thresholds from the database, a logged decision per draft,
and GET /tickets/{id}/decision."""

import asyncio
import sys
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import settings
from app.models import GateThresholds
from test_confidence_gate import _admin_token, _department_id_sync, _register_and_login

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "ai"))
from gate.service import Thresholds, lane_for  # noqa: E402


def test_lane_rules():
    t = Thresholds("t", fast=0.9, assisted=0.5)
    assert lane_for(0.95, True, t) == "fast"
    assert lane_for(0.7, True, t) == "assisted"
    assert lane_for(0.3, True, t) == "escalate"
    assert lane_for(0.99, False, t) == "escalate"  # cannot answer: always escalate
    assert lane_for(0.99, True, Thresholds("t", None, 0.5)) == "assisted"  # uncertified fast lane stays closed
    assert lane_for(0.99, True, None) == "escalate"  # no active thresholds


def _activate(fast, assisted, version):
    async def _go():
        engine = create_async_engine(settings.database_url)
        async with async_sessionmaker(engine, expire_on_commit=False)() as db:
            await db.execute(text("UPDATE gate_thresholds SET active = false"))
            db.add(GateThresholds(version=version, model_version="confidence-v1-judge", label_source="judge",
                                  alpha_fast=0.1, alpha_assisted=0.4, delta=0.1, fast_threshold=fast,
                                  assisted_threshold=assisted, calibration={}, active=True))
            await db.commit()
        await engine.dispose()

    asyncio.run(_go())


def test_every_drafted_ticket_gets_a_logged_explainable_decision(api):
    _department_id_sync("Networking")
    _activate(None, 0.05, "t-test-1")
    admin = _admin_token(api, "gate_admin@example.com")
    customer = _register_and_login(api, "gate_customer@example.com")
    ticket_id = api.post(
        "/tickets",
        data={"subject": "VPN not connecting from home", "description": "My VPN client hangs on connecting today"},
        headers={"Authorization": f"Bearer {customer}"},
    ).json()["id"]

    resp = api.get(f"/tickets/{ticket_id}/decision", headers={"Authorization": f"Bearer {admin}"})
    assert resp.status_code == 200
    d = resp.json()
    assert d["lane"] in ("assisted", "escalate") and d["thresholds_version"] == "t-test-1"
    assert d["label_source"] == "judge" and d["fast_threshold"] is None
    assert d["score"] is not None and 0 <= d["score"] <= 1
    assert isinstance(d["reasons"], list) and len(d["reasons"]) <= 3

    assert api.get(f"/tickets/{ticket_id}/decision",
                   headers={"Authorization": f"Bearer {customer}"}).status_code == 403


def test_decision_is_404_before_any_draft(api):
    admin = _admin_token(api, "gate_admin2@example.com")
    customer = _register_and_login(api, "gate_customer2@example.com")
    ticket_id = api.post("/tickets", data={"subject": "x issue", "description": "nothing routes this"},
                         headers={"Authorization": f"Bearer {customer}"}).json()["id"]
    assert api.get(f"/tickets/{ticket_id}/decision", headers={"Authorization": f"Bearer {admin}"}).status_code == 404


def test_admin_sees_the_error_budget_and_history(api):
    _activate(None, 0.05, "t-test-a")
    _activate(0.9, 0.4, "t-test-b")
    admin = _admin_token(api, "gate_admin3@example.com")
    body = api.get("/gate/thresholds", headers={"Authorization": f"Bearer {admin}"}).json()
    assert body["active"]["version"] == "t-test-b" and body["active"]["fast_threshold"] == 0.9
    history = [h for h in body["history"] if h["version"] != "test-default"]
    assert [h["version"] for h in history] == ["t-test-b", "t-test-a"]
    assert [h["active"] for h in history] == [True, False]  # old sets kept, never deleted


def test_only_admins_see_the_error_budget(api):
    customer = _register_and_login(api, "gate_customer3@example.com")
    assert api.get("/gate/thresholds", headers={"Authorization": f"Bearer {customer}"}).status_code == 403


def test_shift_guard_escalates_drafts_that_look_unlike_the_calibration_data():
    from gate.service import guard_reasons

    t = Thresholds("t", fast=0.9, assisted=0.1, min_dept_prob=0.6, min_probe_margin=0.05)
    confident = {"rt_dept_max_prob": 0.95, "rt_probe_margin": 0.2}
    unsure = {"rt_dept_max_prob": 0.4, "rt_probe_margin": 0.2}
    lookalike = {"rt_dept_max_prob": 0.95, "rt_probe_margin": 0.01}
    assert guard_reasons(confident, t) == []
    assert guard_reasons(unsure, t) == ["uncertain routing: possibly outside the knowledge base"]
    assert guard_reasons(lookalike, t) == ["another department matches as well"]
    assert guard_reasons({}, Thresholds("t", 0.9, 0.1)) == []  # guard off
    assert lane_for(0.99, True, t, guarded=True) == "escalate"


def test_guarded_live_ticket_escalates_to_the_senior_queue(api):
    from gate_seed import set_thresholds

    _department_id_sync("Networking")
    set_thresholds(fast=None, assisted=0.0, version="t-guard", guard={"min_dept_prob": 1.01})  # nothing passes
    admin = _admin_token(api, "gate_admin4@example.com")
    customer = _register_and_login(api, "gate_customer4@example.com")
    ticket_id = api.post(
        "/tickets",
        data={"subject": "VPN not connecting from home", "description": "My VPN client hangs on connecting today"},
        headers={"Authorization": f"Bearer {customer}"},
    ).json()["id"]
    ticket = api.get(f"/tickets/{ticket_id}", headers={"Authorization": f"Bearer {admin}"}).json()
    assert ticket["status"] == "escalated" and ticket["lane"] == "escalate" and ticket["ai_draft_reply"] is None
    escalation = api.get(f"/tickets/{ticket_id}/escalation", headers={"Authorization": f"Bearer {admin}"}).json()
    assert escalation["reason"].startswith("Shift guard: uncertain routing")


def test_queue_can_be_filtered_by_lane(api):
    _department_id_sync("Networking")
    admin = _admin_token(api, "gate_admin5@example.com")
    customer = _register_and_login(api, "gate_customer5@example.com")
    api.post("/tickets", data={"subject": "VPN not connecting from home", "description": "VPN hangs on connecting"},
             headers={"Authorization": f"Bearer {customer}"})
    h = {"Authorization": f"Bearer {admin}"}
    assisted = api.get("/tickets?lane=assisted", headers=h).json()
    assert assisted and all(t["lane"] == "assisted" for t in assisted)
    assert api.get("/tickets?lane=fast", headers=h).json() == []
