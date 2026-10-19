"""Reviewer workbench (Week 7): engineer decisions carry reason codes and time taken."""

import asyncio

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.config import settings
from test_confidence_gate import _department_id_sync, _make_engineer_sync, _register_and_login


def _drafted_ticket(api, suffix: str) -> tuple[str, dict]:
    networking_id = _department_id_sync("Networking")
    _make_engineer_sync(f"wb_eng_{suffix}@example.com", networking_id)
    token = api.post(
        "/auth/login", data={"username": f"wb_eng_{suffix}@example.com", "password": "password123"}
    ).json()["access_token"]
    customer = _register_and_login(api, f"wb_customer_{suffix}@example.com")
    ticket_id = api.post(
        "/tickets",
        data={"subject": "VPN not connecting from home", "description": "My VPN client hangs on connecting today"},
        headers={"Authorization": f"Bearer {customer}"},
    ).json()["id"]
    return ticket_id, {"Authorization": f"Bearer {token}"}


def _feedback_row(ticket_id: str):
    async def _get():
        engine = create_async_engine(settings.database_url)
        async with engine.connect() as conn:
            row = (await conn.execute(text(
                "SELECT action, reason_codes, time_taken_ms FROM feedback WHERE ticket_id = :t"), {"t": ticket_id})).one()
        await engine.dispose()
        return row

    return asyncio.run(_get())


def test_edit_records_reason_codes_and_time_taken(api):
    ticket_id, headers = _drafted_ticket(api, "edit")
    resp = api.post(
        f"/tickets/{ticket_id}/feedback",
        json={"action": "edit", "edited_reply": "1. Restart the VPN client.", "reason_codes": ["missing_step", "tone"],
              "time_taken_ms": 41_250},
        headers=headers,
    )
    assert resp.status_code == 201
    assert tuple(_feedback_row(ticket_id)) == ("edit", ["missing_step", "tone"], 41_250)


def test_unknown_reason_code_is_rejected(api):
    ticket_id, headers = _drafted_ticket(api, "badcode")
    resp = api.post(
        f"/tickets/{ticket_id}/feedback",
        json={"action": "reject", "reject_reason": "wrong", "reason_codes": ["looks_bad"]},
        headers=headers,
    )
    assert resp.status_code == 422


def test_v1_clients_without_the_new_fields_still_work(api):
    ticket_id, headers = _drafted_ticket(api, "v1")
    assert api.post(f"/tickets/{ticket_id}/feedback", json={"action": "accept"}, headers=headers).status_code == 201
    assert tuple(_feedback_row(ticket_id)) == ("accept", [], None)
