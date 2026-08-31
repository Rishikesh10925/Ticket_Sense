"""TicketState: the shared state LangGraph threads through the pipeline's nodes,
merging each node's partial return value into the running state after every step
(LangGraph's standard shallow-update reducer behavior) — see nodes.py.

Deliberately a plain TypedDict, not a Pydantic model: StateGraph expects a mapping
type, and this project's graph runs in-process for a single ticket with no
checkpointer configured (see docs/langgraph-pipeline.md), so nothing here needs to
survive serialization between runs.
"""

from typing import Any, TypedDict


class TicketState(TypedDict, total=False):
    ticket_id: str
    subject: str
    description: str
    department_name: str | None
    department_id: str | None
    priority: str | None
    sentiment: str | None
    evidence: list[Any]  # list[embeddings.retrieve.EvidenceResult]
    draft: str | None
    citations: list[dict]
