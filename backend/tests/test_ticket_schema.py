import uuid
from datetime import datetime, timezone
from types import SimpleNamespace

from app.schemas.tickets import CUSTOMER_READY_CONFIDENCE_THRESHOLD, build_ticket_out

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


def test_high_confidence_ready_true_above_customer_threshold():
    ticket = _fake_ticket(status="drafted", confidence_score=CUSTOMER_READY_CONFIDENCE_THRESHOLD + 0.01)
    out = build_ticket_out(ticket, role="end_user")
    assert out.high_confidence_ready is True


def test_high_confidence_ready_false_at_exactly_the_gate_threshold_but_below_customer_bar():
    # A ticket can clear its department's own (much lower) gate threshold and still
    # not clear the separate, higher customer-facing readiness bar.
    ticket = _fake_ticket(status="drafted", confidence_score=0.6, confidence_threshold=0.45)
    out = build_ticket_out(ticket, role="end_user")
    assert out.high_confidence_ready is False


def test_high_confidence_ready_false_when_not_drafted():
    # A high score on an already-reviewed or escalated ticket isn't "awaiting
    # approval" — that phase is over — so this must not read as ready either.
    ticket = _fake_ticket(status="reviewed", confidence_score=0.99)
    out = build_ticket_out(ticket, role="end_user")
    assert out.high_confidence_ready is False


def test_high_confidence_ready_false_when_score_missing():
    ticket = _fake_ticket(status="drafted", confidence_score=None)
    out = build_ticket_out(ticket, role="end_user")
    assert out.high_confidence_ready is False


def test_high_confidence_ready_visible_to_end_user_despite_score_being_hidden():
    ticket = _fake_ticket(status="drafted", confidence_score=0.9)
    out = build_ticket_out(ticket, role="end_user")
    assert out.high_confidence_ready is True
    assert out.confidence_score is None  # the real score itself stays hidden
    assert out.ai_draft_reply is None  # and so does the draft text


def test_high_confidence_ready_also_set_for_engineer_and_admin_roles():
    ticket = _fake_ticket(status="drafted", confidence_score=0.9)
    for role in ("department_engineer", "admin"):
        out = build_ticket_out(ticket, role=role)
        assert out.high_confidence_ready is True
        assert out.confidence_score == 0.9  # unlike end_user, these roles still see the real score
