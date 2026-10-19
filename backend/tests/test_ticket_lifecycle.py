import pytest

from app.services.ticket_lifecycle import TicketStatus, can_transition, transition


def test_valid_forward_transitions():
    assert can_transition(TicketStatus.SUBMITTED, TicketStatus.CLASSIFIED)
    assert can_transition(TicketStatus.CLASSIFIED, TicketStatus.ROUTED)
    assert can_transition(TicketStatus.ROUTED, TicketStatus.DRAFTED)
    assert can_transition(TicketStatus.DRAFTED, TicketStatus.REVIEWED)
    assert can_transition(TicketStatus.REVIEWED, TicketStatus.CLOSED)


def test_closed_is_terminal():
    assert not can_transition(TicketStatus.CLOSED, TicketStatus.SUBMITTED)
    assert not can_transition(TicketStatus.CLOSED, TicketStatus.CLASSIFIED)


def test_cannot_skip_states():
    assert not can_transition(TicketStatus.SUBMITTED, TicketStatus.ROUTED)
    assert not can_transition(TicketStatus.SUBMITTED, TicketStatus.CLOSED)


def test_cannot_go_backwards():
    assert not can_transition(TicketStatus.ROUTED, TicketStatus.SUBMITTED)


def test_transition_raises_on_invalid():
    with pytest.raises(ValueError):
        transition(TicketStatus.SUBMITTED, TicketStatus.CLOSED)


def test_transition_returns_target_on_valid():
    assert transition(TicketStatus.SUBMITTED, TicketStatus.CLASSIFIED) == TicketStatus.CLASSIFIED


def test_routed_can_branch_to_escalated_or_drafted():
    # The Week 9 confidence gate: a routed ticket goes to DRAFTED (gate passed) or
    # straight to ESCALATED (gate failed, no draft shown) — never both from one ticket,
    # but both are individually valid next states.
    assert can_transition(TicketStatus.ROUTED, TicketStatus.DRAFTED)
    assert can_transition(TicketStatus.ROUTED, TicketStatus.ESCALATED)


def test_drafted_can_branch_to_reviewed_or_escalated():
    # A reviewer can act on a draft (REVIEWED) or choose to escalate it instead
    # (ESCALATED) — see app/routers/tickets.py's feedback endpoint.
    assert can_transition(TicketStatus.DRAFTED, TicketStatus.REVIEWED)
    assert can_transition(TicketStatus.DRAFTED, TicketStatus.ESCALATED)


def test_escalated_reaches_closed():
    assert can_transition(TicketStatus.ESCALATED, TicketStatus.CLOSED)


def test_escalated_is_not_terminal_before_closed():
    assert not can_transition(TicketStatus.ESCALATED, TicketStatus.SUBMITTED)
    assert not can_transition(TicketStatus.ESCALATED, TicketStatus.DRAFTED)
