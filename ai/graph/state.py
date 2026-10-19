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
    attachment_path: str | None
    attachment_type: str | None
    attachment_text: str | None
    ocr_confidence: float | None
    redacted_subject: str  # PII-redacted copies: the only text models and logs see
    redacted_description: str
    redacted_attachment: str | None
    redaction_map: dict[str, str]  # placeholder -> original; stored on the ticket, never logged
    department_name: str | None
    department_id: str | None
    priority: str | None
    sentiment: str | None
    classification: dict | None  # classifier v2 labels with max_prob, entropy, probabilities
    evidence: list[Any]  # list[embeddings.retrieve.EvidenceResult]
    retrieval_probe: float | None  # best dense match in another department (routing signal)
    retrieval_run_id: str | None
    passages: list[dict]  # numbered evidence the drafter saw: n, article_id, article_key, chunk_id, title, text
    draft_result: dict | None  # structured draft: schema_valid, can_answer, steps, rejection, shown, ...
    grounding: dict | None  # claim check: groundedness, min/mean support, claims, weakest
    retrieval_candidates: list[dict]  # every fused candidate with its ranks and scores
    signals: dict | None  # the signal vector (ai/signals/features.py)
    draft: str | None  # rendered reply text, only when the draft is shown
    citations: list[dict]
    confidence_score: float | None
    confidence_features: dict | None
    confidence_threshold: float | None
    gate_decision: str | None  # "draft" | "escalate" — see nodes.py's gate_condition
