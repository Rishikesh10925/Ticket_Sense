import uuid
from datetime import datetime, timezone
from types import SimpleNamespace

from app.schemas.tickets import build_ticket_out

NOW = datetime.now(timezone.utc)


def _fake_ticket(**overrides) -> SimpleNamespace:
    defaults = dict(
        id=uuid.uuid4(),
        submitted_by=uuid.uuid4(),
        department_id=uuid.uuid4(),
        subject="Subject",
        description="Description",
        attachment_path=None,
        attachment_type=None,
        attachment_text=None,
        ocr_confidence=None,
        priority="medium",
        sentiment="neutral",
        status="drafted",
        ai_draft_reply="Based on the retrieved evidence: ...",
        ai_draft_citations=[],
        confidence_score=0.5,
        confidence_features={
            "retrieval_relevance": 0.5,
            "ticket_resolution_similarity": 0.5,
            "document_freshness": 0.5,
            "ocr_confidence": 1.0,
            "category_risk": 0.5,
        },
        confidence_threshold=0.5,
        created_at=NOW,
        updated_at=NOW,
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def test_final_response_null_when_not_reviewed():
    ticket = _fake_ticket(status="drafted")
    out = build_ticket_out(ticket, role="end_user", final_response=None)
    assert out.final_response is None


def test_final_response_visible_to_end_user_once_reviewed():
    ticket = _fake_ticket(status="reviewed")
    out = build_ticket_out(ticket, role="end_user", final_response="Restart the VPN client and retry.")
    assert out.final_response == "Restart the VPN client and retry."
    # The internal draft/score stay hidden from end_user exactly as before -- only
    # the caller-computed final_response is customer-visible.
    assert out.ai_draft_reply is None
    assert out.confidence_score is None


def test_final_response_also_visible_to_engineer_and_admin():
    ticket = _fake_ticket(status="reviewed")
    for role in ("department_engineer", "admin"):
        out = build_ticket_out(ticket, role=role, final_response="Restart the VPN client and retry.")
        assert out.final_response == "Restart the VPN client and retry."


def test_build_ticket_out_defaults_final_response_to_none_when_not_passed():
    ticket = _fake_ticket(status="reviewed")
    out = build_ticket_out(ticket, role="end_user")
    assert out.final_response is None
