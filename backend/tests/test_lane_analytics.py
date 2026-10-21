"""GET /analytics/lanes: lane mix, engineer actions, latency and confidence per lane."""

from test_confidence_gate import _admin_token, _department_id_sync, _make_engineer_sync, _register_and_login


def test_lane_dashboard_counts_live_tickets_and_engineer_actions(api):
    networking = _department_id_sync("Networking")
    _make_engineer_sync("lanes_eng@example.com", networking)
    eng = api.post("/auth/login", data={"username": "lanes_eng@example.com", "password": "password123"}).json()["access_token"]
    customer = _register_and_login(api, "lanes_customer@example.com")
    ticket_id = api.post("/tickets", data={"subject": "VPN not connecting from home", "description": "VPN hangs on connecting"},
                         headers={"Authorization": f"Bearer {customer}"}).json()["id"]
    api.post(f"/tickets/{ticket_id}/feedback", json={"action": "accept", "time_taken_ms": 30_000},
             headers={"Authorization": f"Bearer {eng}"})

    admin = _admin_token(api, "lanes_admin@example.com")
    body = api.get("/analytics/lanes", headers={"Authorization": f"Bearer {admin}"}).json()
    assert body["lane_mix"] == {"fast": 0, "assisted": 1, "escalate": 0} and body["total"] == 1
    assert body["actions"]["assisted"] == {"accept": 1}
    assert body["acceptance_rate"]["assisted"] == 1.0 and body["acceptance_rate"]["fast"] is None
    assert body["median_decision_ms"]["assisted"] == 30_000
    assert body["median_pipeline_ms"]["assisted"] is not None
    assert sum(body["confidence_bins"]["assisted"]) == 1


def test_lane_dashboard_is_admin_only(api):
    customer = _register_and_login(api, "lanes_customer2@example.com")
    assert api.get("/analytics/lanes", headers={"Authorization": f"Bearer {customer}"}).status_code == 403
