"""Node factories for the ticket-processing LangGraph pipeline.

Each factory returns an async node function — `(TicketState) -> dict` — that closes
over whatever per-run dependencies it needs (a request-scoped AsyncSession, the
Department model, the LLM client, the claim scorer). TicketState itself stays a plain
dict of ticket data, not a place to smuggle non-serializable objects like a DB session
through the graph. See docs/langgraph-pipeline.md and pipeline.py, which wires these
into the actual StateGraph.

Blueprint V2 §9 stages 1 to 5 (intake, classify, retrieve, draft, check) run for every
ticket; the gate comes after the check because the claim scores are among its inputs.
"""

import asyncio
import os
import re
import sys
from functools import lru_cache
from pathlib import Path
from uuid import UUID

_AI_DIR = Path(__file__).resolve().parents[1]
if str(_AI_DIR) not in sys.path:
    sys.path.insert(0, str(_AI_DIR))

from sqlalchemy import select  # noqa: E402

from confidence.features import compute_features  # noqa: E402
from confidence.predict import predict_confidence  # noqa: E402
from generation.drafting import Passage, generate_draft  # noqa: E402
from generation.llm import LLMClient, LLMError  # noqa: E402
from grounding.claims import Scorer, check_draft, nli_scorer  # noqa: E402
from models.classifier import classify_ticket  # noqa: E402
from models.classifier_v2 import ARTIFACT as CLASSIFIER_V2  # noqa: E402
from ocr.extract import extract_attachment_text  # noqa: E402
from retrieval.hybrid import hybrid_search  # noqa: E402
from retrieval.run_log import log_run, to_evidence  # noqa: E402
from security.output_screen import SCREEN_VERSION, screen  # noqa: E402
from security.pii import redact  # noqa: E402

from graph.state import TicketState  # noqa: E402

WEAKEST_CLAIMS = 3  # shown in the assisted lane (Blueprint V2 §9.1)
_WORD = re.compile(r"[a-z0-9]+")


def _subject(state: TicketState) -> str:
    return state.get("redacted_subject", state["subject"])


def _description(state: TicketState) -> str:
    return state.get("redacted_description", state["description"])


def _attachment(state: TicketState) -> str | None:
    return state.get("redacted_attachment", state.get("attachment_text"))


def _augmented_description(state: TicketState) -> str:
    """The (redacted) ticket description, with any extracted attachment text folded in —
    used everywhere classify/retrieve would otherwise read the description alone, so
    OCR/PDF/log text actually feeds into classification and retrieval rather than just
    sitting on the ticket record unused. See docs/langgraph-pipeline.md."""
    description = _description(state)
    attachment_text = _attachment(state)
    if attachment_text:
        return f"{description}\n\n[Extracted from attachment]\n{attachment_text}"
    return description


def lexical_scorer(pairs: list[tuple[str, str]]) -> list[float]:
    """Share of the claim's words found in the passage. A cheap stand-in for the NLI
    model in CI and tests (GROUNDING_SCORER=lexical); never used for reported results."""
    scores = []
    for premise, claim in pairs:
        words = set(_WORD.findall(claim.lower()))
        scores.append(len(words & set(_WORD.findall(premise.lower()))) / len(words) if words else 0.0)
    return scores


def get_scorer(name: str | None = None) -> Scorer:
    name = name or os.environ.get("GROUNDING_SCORER", "nli")
    return {"nli": nli_scorer, "lexical": lexical_scorer}[name]


def render_draft(steps: list[dict]) -> str:
    """The numbered reply text an engineer edits, with [n] citation markers."""
    return "\n".join(
        f"{i}. {step['text']} " + "".join(f"[{n}]" for n in step["citations"]) for i, step in enumerate(steps, start=1)
    )


def make_extract_node():
    async def node(state: TicketState) -> dict:
        attachment_path = state.get("attachment_path")
        attachment_type = state.get("attachment_type")
        if not attachment_path or not attachment_type:
            return {"attachment_text": None, "ocr_confidence": None}

        result = extract_attachment_text(attachment_path, attachment_type)
        return {"attachment_text": result.text or None, "ocr_confidence": result.confidence}

    return node


def make_redact_node():
    """Blueprint V2 §9 stage 1: PII is redacted before any model call or log. Every
    later node reads only the redacted fields; the map stays in state for the service
    to store on the ticket row."""

    async def node(state: TicketState) -> dict:
        mapping: dict[str, str] = {}
        subject = redact(state["subject"], mapping).text
        description = redact(state["description"], mapping).text
        attachment = redact(state.get("attachment_text"), mapping).text or None
        return {
            "redacted_subject": subject,
            "redacted_description": description,
            "redacted_attachment": attachment,
            "redaction_map": mapping,
        }

    return node


@lru_cache(maxsize=1)
def _classifier_v2():
    """Classifier v2 (Week 4): embeddings plus TF-IDF, trained on the benchmark train
    split. None if the artifact is absent, in which case the V1 models route."""
    if not CLASSIFIER_V2.exists():
        return None
    from models.classifier_v2 import TicketClassifier

    return TicketClassifier.load(CLASSIFIER_V2)


def _uncertainty(prediction) -> dict:
    return {
        "label": prediction.label,
        "max_prob": round(prediction.max_prob, 4),
        "entropy": round(prediction.entropy, 4),
        "probabilities": {k: round(v, 4) for k, v in prediction.probabilities.items()},
    }


def make_classify_node():
    """Department and priority from classifier v2, with its uncertainty (maximum class
    probability and normalised entropy) kept in state as a confidence signal (Blueprint
    V2 §9 stage 2). Sentiment still comes from the V1 model, which v2 does not replace."""

    async def node(state: TicketState) -> dict:
        subject, description = _subject(state), _augmented_description(state)
        v1 = classify_ticket(subject, description)
        classifier = _classifier_v2()
        if classifier is None:
            return {"department_name": v1.department, "priority": v1.priority, "sentiment": v1.sentiment,
                    "classification": None}
        prediction = (await asyncio.to_thread(classifier.predict, [f"{subject}\n\n{description}"]))[0]
        return {
            "department_name": prediction["department"].label,
            "priority": prediction["priority"].label,
            "sentiment": v1.sentiment,
            "classification": {
                "model": "classifier-v2",
                "department": _uncertainty(prediction["department"]),
                "priority": _uncertainty(prediction["priority"]),
            },
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
            return {"evidence": [], "passages": [], "retrieval_run_id": None}

        # Hybrid retrieval over kb_chunks (keyword + dense, RRF, cross-encoder rerank),
        # department- and served-scoped in the SQL. Every run is logged with all
        # candidate scores, and the evidence endpoint reads that log back.
        query_text = f"{_subject(state)}\n\n{_augmented_description(state)}"
        result = await hybrid_search(db, query_text, UUID(department_id), k=5)
        ticket_id = state.get("ticket_id")
        run = await log_run(db, result, UUID(ticket_id) if ticket_id else None)
        passages = [
            {
                "n": n,
                "article_id": str(h.article_id),
                "article_key": h.article_key,
                "chunk_id": str(h.chunk_id),
                "title": h.title,
                "text": h.text,
            }
            for n, h in enumerate(result.hits, start=1)
        ]
        return {
            "evidence": to_evidence(result),
            "passages": passages,
            "retrieval_run_id": str(run.id),
            "retrieval_probe": result.probe_top1_similarity,
        }

    return node


def make_draft_node(llm_client: LLMClient):
    async def node(state: TicketState) -> dict:
        passages = state.get("passages") or []
        try:
            # The client call is blocking (HTTP to the model server); keep it off the loop.
            result = await asyncio.to_thread(
                generate_draft,
                llm_client,
                f"{_subject(state)}\n\n{_description(state)}",
                _attachment(state),
                [Passage(p["n"], p["title"], p["text"], p.get("article_key")) for p in passages],
            )
        except LLMError as exc:
            return {
                "draft_result": {"schema_valid": False, "rejection": f"model unavailable: {exc}", "shown": False},
                "draft": None,
                "citations": [],
            }

        by_n = {p["n"]: p for p in passages}
        # Injection defences v2: anything runnable in a step (URL, command, code) must
        # come from a passage that step cites, or nobody sees the draft.
        screened = screen(result.steps, {p["n"]: p["text"] for p in passages}) if result.shown else None
        shown = result.shown and not (screened and screened.blocked)
        rejection = result.rejection or (f"screen: {screened.reasons[0]}" if screened and screened.blocked else None)
        cited = list(dict.fromkeys(n for step in result.steps for n in step["citations"]))
        citations = [
            {
                "n": n,
                "source_type": "knowledge_base",
                "source_id": by_n[n]["article_id"],
                "article_key": by_n[n]["article_key"],
                "title": by_n[n]["title"],
            }
            for n in cited
        ]
        resp_logprobs = result.token_logprobs or []
        return {
            "draft_result": {
                "schema_valid": result.schema_valid,
                "can_answer": result.can_answer,
                "steps": result.steps,
                "missing_information": result.missing_information,
                "raw_text": result.raw_text,
                "model": result.model,
                "prompt_version": result.prompt_version,
                "rejection": rejection,
                "shown": shown,
                "screen": {"version": SCREEN_VERSION, "blocked": bool(screened and screened.blocked),
                           "reasons": list(screened.reasons) if screened else []},
                "mean_logprob": (sum(resp_logprobs) / len(resp_logprobs)) if resp_logprobs else None,
            },
            "draft": render_draft(result.steps) if shown else None,
            "citations": citations if shown else [],
        }

    return node


def make_check_node(scorer: Scorer | None = None):
    async def node(state: TicketState) -> dict:
        draft = state.get("draft_result") or {}
        if not draft.get("shown"):
            return {"grounding": None}
        passages = {p["n"]: p["text"] for p in state.get("passages") or []}
        grounding = await asyncio.to_thread(check_draft, draft["steps"], passages, scorer or get_scorer())
        claims = [
            {
                "step_index": c.step_index,
                "claim_index": c.claim_index,
                "text": c.text,
                "cited": list(c.cited),
                "support": c.support,
            }
            for c in grounding.claims
        ]
        return {
            "grounding": {
                "groundedness": grounding.groundedness,
                "min_support": grounding.min_support,
                "mean_support": grounding.mean_support,
                "claims": claims,
                "weakest": [
                    {"step_index": c.step_index, "text": c.text, "support": c.support}
                    for c in grounding.weakest(WEAKEST_CLAIMS)
                ],
            }
        }

    return node


def make_score_node(db, department_model, default_threshold: float):
    """Interim V1 confidence score until the Week 8 confidence model replaces it."""

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


def gate_condition(state: TicketState) -> str:
    """Routes to "draft" (shown to the engineer) or "escalate" (no AI draft) — a
    LangGraph conditional edge (see pipeline.py), not an if/else buried inside a node,
    so the routing decision is visible in the graph definition itself.

    A draft that failed the schema, or that says the evidence cannot answer the ticket,
    always escalates (Blueprint V2 §9.1). Otherwise the score must clear the
    department's threshold. The Week 9 gate replaces this with two LTT thresholds."""
    draft = state.get("draft_result")
    if draft is not None and not draft.get("shown"):
        return "escalate"
    score = state.get("confidence_score")
    threshold = state.get("confidence_threshold")
    if score is None or threshold is None:
        # Shouldn't happen (score always runs first), but fails open to showing the
        # draft rather than crashing the pipeline on an unexpected state shape.
        return "draft"
    return "draft" if score >= threshold else "escalate"


def make_show_node():
    async def node(state: TicketState) -> dict:
        return {"gate_decision": "draft"}

    return node


def make_escalate_node():
    async def node(state: TicketState) -> dict:
        return {"gate_decision": "escalate"}

    return node
