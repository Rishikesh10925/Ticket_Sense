from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.models.portal import PORTAL_FIELDS

AssistState = Literal["processing", "answer", "portal", "resolved", "closed"]


class AssistSource(BaseModel):
    title: str


class AssistPortal(BaseModel):
    id: UUID
    name: str
    url: str
    field_map: dict[str, str]
    reference_selector: str | None
    # The values the extension writes into the form (the submitter's own ticket text).
    values: dict[str, str]


class AssistOut(BaseModel):
    """What the browser extension shows for one of the user's tickets.

    `answer` is set only in the fast and assisted lanes; `verify` is true in the assisted
    lane, where the draft has not been certified and the user is told to check it. The
    portal is offered whenever the ticket is not resolved, so a user whose answer did not
    help can still file a complaint."""

    ticket_id: UUID
    status: str
    lane: str | None
    state: AssistState
    message: str
    answer: str | None = None
    verify: bool = False
    sources: list[AssistSource] = []
    final_response: str | None = None
    portal: AssistPortal | None = None
    portal_reference: str | None = None
    portal_submitted_at: datetime | None = None


class PortalReferenceIn(BaseModel):
    reference: str = Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9][A-Za-z0-9._/\-]*$")
    portal_id: UUID | None = None


def _check_field_map(v: dict[str, str]) -> dict[str, str]:
    unknown = sorted(set(v) - set(PORTAL_FIELDS))
    if unknown:
        raise ValueError(f"unknown ticket fields {unknown}; allowed: {list(PORTAL_FIELDS)}")
    for key, selector in v.items():
        if not selector.strip() or len(selector) > 255:
            raise ValueError(f"selector for {key!r} must be 1 to 255 characters")
    return v


class PortalIn(BaseModel):
    department_id: UUID | None = None
    name: str = Field(min_length=1, max_length=120)
    url: str = Field(min_length=8, max_length=512, pattern=r"^https?://\S+$")
    field_map: dict[str, str] = {}
    reference_selector: str | None = Field(default=None, max_length=255)
    active: bool = True

    @field_validator("field_map")
    @classmethod
    def _fields(cls, v: dict[str, str]) -> dict[str, str]:
        return _check_field_map(v)


class PortalOut(BaseModel):
    id: UUID
    department_id: UUID | None
    department_name: str | None
    name: str
    url: str
    field_map: dict[str, str]
    reference_selector: str | None
    active: bool
    updated_at: datetime
