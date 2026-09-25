from enum import StrEnum


class TicketStatus(StrEnum):
    SUBMITTED = "submitted"
    CLASSIFIED = "classified"
    ROUTED = "routed"
    DRAFTED = "drafted"
    REVIEWED = "reviewed"
    ESCALATED = "escalated"
    CLOSED = "closed"


# Branching lifecycle per docs/ticket-lifecycle.md and docs/architecture.md's
# confidence gate (Week 9): ROUTED can advance to either DRAFTED (the gate passed —
# confidence_score >= confidence_threshold) or ESCALATED (the gate failed, no draft is
# shown to a human — see docs/langgraph-pipeline.md). DRAFTED can advance to REVIEWED
# (a reviewer accepted/edited/rejected the draft, or the confidence score cleared the
# separate auto-resolution bar with no reviewer at all — see app/services/pipeline.py)
# or ESCALATED (a reviewer chose to escalate/doubt a drafted ticket instead of acting
# on it — see app/routers/tickets.py's feedback endpoint). ESCALATED can now also
# reach REVIEWED directly: once an admin approves the escalation and assigns it to a
# specific engineer (see app/routers/escalations.py), that engineer resolves it with
# their own written response — there was never a draft to review, but the outcome is
# the same "a human-approved response now exists" state. CLOSED is terminal, reachable
# from either REVIEWED or ESCALATED (an admin rejecting an escalation outright, with no
# response ever generated).
_VALID_TRANSITIONS: dict[TicketStatus, set[TicketStatus]] = {
    TicketStatus.SUBMITTED: {TicketStatus.CLASSIFIED},
    TicketStatus.CLASSIFIED: {TicketStatus.ROUTED},
    TicketStatus.ROUTED: {TicketStatus.DRAFTED, TicketStatus.ESCALATED},
    TicketStatus.DRAFTED: {TicketStatus.REVIEWED, TicketStatus.ESCALATED},
    TicketStatus.REVIEWED: {TicketStatus.CLOSED},
    TicketStatus.ESCALATED: {TicketStatus.CLOSED, TicketStatus.REVIEWED},
}


def can_transition(current: TicketStatus, target: TicketStatus) -> bool:
    return target in _VALID_TRANSITIONS.get(current, set())


def transition(current: TicketStatus, target: TicketStatus) -> TicketStatus:
    if not can_transition(current, target):
        raise ValueError(f"cannot transition ticket from '{current}' to '{target}'")
    return target
