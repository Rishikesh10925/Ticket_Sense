"""Builds and compiles the extract -> classify -> route -> retrieve -> score ->
[confidence gate] -> draft | escalate LangGraph StateGraph for a single ticket. See
docs/langgraph-pipeline.md for the design and docs/langgraph-research.md (Week 1) for
the original target shape this implements.

score runs BEFORE draft (Week 9), not after (Week 8's original order) — scoring only
needs the retrieved evidence, OCR confidence, and routed department, none of which
depend on the draft's text, so the gate can decide whether to draft at all rather than
drafting first and discarding the result. This also matches docs/architecture.md's
"Example" walkthrough: an escalated ticket has no AI draft, not a hidden one.

build_pipeline() is a cheap factory, not a singleton — it's called fresh for every
ticket run because its nodes close over a request-scoped AsyncSession and the selected
LLMProvider (see nodes.py), neither of which should be shared across requests.
"""

import sys
from pathlib import Path

_AI_DIR = Path(__file__).resolve().parents[1]
if str(_AI_DIR) not in sys.path:
    sys.path.insert(0, str(_AI_DIR))

from langgraph.graph import END, StateGraph  # noqa: E402

from graph.nodes import (  # noqa: E402
    gate_condition,
    make_classify_node,
    make_draft_node,
    make_escalate_node,
    make_extract_node,
    make_retrieve_node,
    make_route_node,
    make_score_node,
)
from graph.state import TicketState  # noqa: E402


def build_pipeline(db, department_model, llm_provider, default_confidence_threshold: float = 0.5):
    graph = StateGraph(TicketState)
    graph.add_node("extract", make_extract_node())
    graph.add_node("classify", make_classify_node())
    graph.add_node("route", make_route_node(db, department_model))
    graph.add_node("retrieve", make_retrieve_node(db))
    graph.add_node("score", make_score_node(db, department_model, default_confidence_threshold))
    graph.add_node("draft", make_draft_node(llm_provider))
    graph.add_node("escalate", make_escalate_node())

    graph.set_entry_point("extract")
    graph.add_edge("extract", "classify")
    graph.add_edge("classify", "route")
    graph.add_edge("route", "retrieve")
    graph.add_edge("retrieve", "score")
    graph.add_conditional_edges("score", gate_condition, {"draft": "draft", "escalate": "escalate"})
    graph.add_edge("draft", END)
    graph.add_edge("escalate", END)

    return graph.compile()
