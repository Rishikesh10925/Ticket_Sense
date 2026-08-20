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
