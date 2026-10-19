from pathlib import Path

SAMPLE_IMAGE = Path(__file__).resolve().parents[2] / "data" / "sample_screenshots" / "networking_vpn_error.png"


def _register_and_login(api, email: str) -> str:
    api.post("/auth/register", json={"email": email, "full_name": "Test User", "password": "password123"})
    resp = api.post("/auth/login", data={"username": email, "password": "password123"})
    return resp.json()["access_token"]


def test_ticket_with_image_attachment_gets_ocr_text(api):
    token = _register_and_login(api, "sasha@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    with open(SAMPLE_IMAGE, "rb") as f:
        create_resp = api.post(
            "/tickets",
            data={"subject": "VPN broken again", "description": "Screenshot attached."},
            files={"attachment": ("vpn_error.png", f, "image/png")},
            headers=headers,
        )
    assert create_resp.status_code == 201
    ticket_id = create_resp.json()["id"]

    # The pipeline (extract -> classify -> route -> retrieve -> draft) has already
    # run as a background task by the time this next request comes in — see
    # test_classification.py's test_ticket_auto_classified_and_routed for why a
    # single follow-up GET, not a poll loop, is enough with TestClient.
    ticket = api.get(f"/tickets/{ticket_id}", headers=headers).json()

    assert ticket["attachment_text"]
    assert "VPN" in ticket["attachment_text"]
    assert ticket["ocr_confidence"] is not None
    assert 0.0 < ticket["ocr_confidence"] <= 1.0


def test_ticket_without_attachment_has_no_ocr_fields(api):
    token = _register_and_login(api, "taylor@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    create_resp = api.post(
        "/tickets",
        data={"subject": "No attachment here", "description": "Just text, nothing attached."},
        headers=headers,
    )
    ticket_id = create_resp.json()["id"]
    ticket = api.get(f"/tickets/{ticket_id}", headers=headers).json()

    assert ticket["attachment_text"] is None
    assert ticket["ocr_confidence"] is None


def test_attachment_download_returns_file_content(api):
    token = _register_and_login(api, "uma@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    with open(SAMPLE_IMAGE, "rb") as f:
        original_bytes = f.read()
        f.seek(0)
        create_resp = api.post(
            "/tickets",
            data={"subject": "VPN broken", "description": "See attached."},
            files={"attachment": ("vpn_error.png", f, "image/png")},
            headers=headers,
        )
    ticket_id = create_resp.json()["id"]

    resp = api.get(f"/tickets/{ticket_id}/attachment", headers=headers)
    assert resp.status_code == 200
    assert resp.content == original_bytes


def test_attachment_download_requires_ticket_access(api):
    owner_token = _register_and_login(api, "victor@example.com")
    other_token = _register_and_login(api, "wendy@example.com")

    with open(SAMPLE_IMAGE, "rb") as f:
        create_resp = api.post(
            "/tickets",
            data={"subject": "VPN broken", "description": "See attached."},
            files={"attachment": ("vpn_error.png", f, "image/png")},
            headers={"Authorization": f"Bearer {owner_token}"},
        )
    ticket_id = create_resp.json()["id"]

    resp = api.get(f"/tickets/{ticket_id}/attachment", headers={"Authorization": f"Bearer {other_token}"})
    assert resp.status_code == 403


def test_attachment_download_404_when_no_attachment(api):
    token = _register_and_login(api, "xena@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    create_resp = api.post(
        "/tickets",
        data={"subject": "No attachment", "description": "Nothing to see here."},
        headers=headers,
    )
    ticket_id = create_resp.json()["id"]

    resp = api.get(f"/tickets/{ticket_id}/attachment", headers=headers)
    assert resp.status_code == 404
