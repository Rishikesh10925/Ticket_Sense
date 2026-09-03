"""Node factories for the ticket-processing LangGraph pipeline.

Each factory returns an async node function — `(TicketState) -> dict` — that closes
over whatever per-run dependencies it needs (a request-scoped AsyncSession, the
Department model, the selected LLMProvider). TicketState itself stays a plain dict of
ticket data, not a place to smuggle non-serializable objects like a DB session through
the graph. See docs/langgraph-pipeline.md and pipeline.py, which wires these into the
actual StateGraph.
"""

import re
import sys
from pathlib import Path
from uuid import UUID

_AI_DIR = Path(__file__).resolve().parents[1]
if str(_AI_DIR) not in sys.path:
    sys.path.insert(0, str(_AI_DIR))

from sqlalchemy import select  # noqa: E402

from embeddings.retrieve import retrieve_evidence  # noqa: E402
from generation.llm_interface import LLMProvider  # noqa: E402
from generation.prompt import build_prompt  # noqa: E402
from models.classifier import classify_ticket  # noqa: E402
from ocr.extract import extract_attachment_text  # noqa: E402
from confidence.features import compute_features  # noqa: E402
from confidence.predict import predict_confidence  # noqa: E402

from graph.state import TicketState  # noqa: E402

_CITATION_RE = re.compile(r"\[(\d+)\]")


def _augmented_description(state: TicketState) -> str:
    """The ticket description, with any extracted attachment text folded in — used
    everywhere classify/retrieve/draft would otherwise read state["description"]
    alone, so OCR/PDF/log text actually feeds into classification, retrieval, and
    drafting rather than just sitting on the ticket record unused. See
    docs/langgraph-pipeline.md."""
    description = state["description"]
    attachment_text = state.get("attachment_text")
    if attachment_text:
        return f"{description}\n\n[Extracted from attachment]\n{attachment_text}"
    return description


def make_extract_node():
    async def node(state: TicketState) -> dict:
        attachment_path = state.get("attachment_path")
        attachment_type = state.get("attachment_type")
        if not attachment_path or not attachment_type:
            return {"attachment_text": None, "ocr_confidence": None}

        result = extract_attachment_text(attachment_path, attachment_type)
        return {"attachment_text": result.text or None, "ocr_confidence": result.confidence}

    return node


def make_classify_node():
    async def node(state: TicketState) -> dict:
        result = classify_ticket(state["subject"], _augmented_description(state))
        return {
            "department_name": result.department,
            "priority": result.priority,
            "sentiment": result.sentiment,
        }

    return node


def make_route_node(db, department_model):
    async def node(state: TicketState) -> dict:
        department = await db.scalar(
            select(department_model).where(department_model.name == state.get("department_name"))
        )
        return {"department_id": str(department.id) if department is not None else None}

    return node


def make_retrieve_node(db):
    async def node(state: TicketState) -> dict:
        department_id = state.get("department_id")
        if department_id is None:
            # No department to scope the search to yet — same rule as
            # app/services/retrieval.py's get_evidence_for_ticket.
            return {"evidence": []}

        query_text = f"{state['subject']}\n\n{_augmented_description(state)}"
        evidence = await retrieve_evidence(db, query_text, UUID(department_id), k=5)
        return {"evidence": evidence}

    return node


def make_draft_node(llm_provider: LLMProvider):
    async def node(state: TicketState) -> dict:
        evidence = state.get("evidence") or []
        prompt = build_prompt(state["subject"], _augmented_description(state), evidence)
        draft = llm_provider.generate(prompt, evidence)

        # Citations are read back out of the draft's own [n] markers rather than just
        # echoing every retrieved item, so ai_draft_citations reflects what the draft
        # actually cited (in the order it cited them) — see docs/langgraph-pipeline.md.
        citations = []
        seen: set[int] = set()
        for match in _CITATION_RE.finditer(draft):
            n = int(match.group(1))
            if n in seen or not (1 <= n <= len(evidence)):
                continue
            seen.add(n)
            item = evidence[n - 1]
            citations.append(
                {"source_type": item.source_type, "source_id": str(item.source_id), "title": item.title}
            )

        return {"draft": draft, "citations": citations}

    return node


def make_score_node(db, department_model, default_threshold: float):
    async def node(state: TicketState) -> dict:
        features = compute_features(
            state.get("evidence") or [], state.get("ocr_confidence"), state.get("department_name")
        )
        score = predict_confidence(features)

        threshold = default_threshold
        department_id = state.get("department_id")
        if department_id is not None:
            department = await db.get(department_model, UUID(department_id))
            if department is not None:
                threshold = float(department.confidence_threshold)

        return {
            "confidence_score": score,
            "confidence_features": features.to_dict(),
            "confidence_threshold": threshold,
        }

    return node
