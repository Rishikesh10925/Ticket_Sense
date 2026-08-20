from enum import StrEnum


class TicketStatus(StrEnum):
    SUBMITTED = "submitted"
    CLASSIFIED = "classified"
    ROUTED = "routed"
    DRAFTED = "drafted"
    REVIEWED = "reviewed"
    CLOSED = "closed"


# Linear lifecycle per docs/ticket-lifecycle.md: submitted -> classified -> routed ->
# drafted -> reviewed -> closed. Each state only advances to the single next state;
# CLOSED is terminal. Branches (e.g. escalation) aren't part of this chain yet — the
# confidence gate and escalation workflow land in a later week (see architecture.md).
_NEXT_STATUS: dict[TicketStatus, TicketStatus] = {
    TicketStatus.SUBMITTED: TicketStatus.CLASSIFIED,
    TicketStatus.CLASSIFIED: TicketStatus.ROUTED,
    TicketStatus.ROUTED: TicketStatus.DRAFTED,
    TicketStatus.DRAFTED: TicketStatus.REVIEWED,
    TicketStatus.REVIEWED: TicketStatus.CLOSED,
}


def can_transition(current: TicketStatus, target: TicketStatus) -> bool:
    return _NEXT_STATUS.get(current) == target


def transition(current: TicketStatus, target: TicketStatus) -> TicketStatus:
    if not can_transition(current, target):
        raise ValueError(f"cannot transition ticket from '{current}' to '{target}'")
    return target
