"""Builds and compiles the ticket pipeline as a LangGraph StateGraph:

    extract -> redact -> classify -> route -> retrieve -> draft -> check -> signals -> gate -> score
            -> [gate] -> show | escalate

Blueprint V2 §9 stages 1 to 8. Every ticket gets a draft and a claim check, because
the check's scores feed the confidence model; the gate then decides whether the
engineer sees the draft. An escalated ticket's draft is stored for evaluation but never
shown (§9.1, "no AI draft"). See docs/langgraph-pipeline.md.

build_pipeline() is a cheap factory, not a singleton — it's called fresh for every
ticket run because its nodes close over a request-scoped AsyncSession, neither of
which should be shared across requests.
"""

import sys
from pathlib import Path

_AI_DIR = Path(__file__).resolve().parents[1]
if str(_AI_DIR) not in sys.path:
    sys.path.insert(0, str(_AI_DIR))

from langgraph.graph import END, StateGraph  # noqa: E402

from graph.nodes import (  # noqa: E402
    gate_condition,
    make_check_node,
    make_classify_node,
    make_draft_node,
    make_escalate_node,
    make_extract_node,
    make_gate_node,
    make_redact_node,
    make_retrieve_node,
    make_route_node,
    make_score_node,
    make_show_node,
    make_signals_node,
)
from graph.state import TicketState  # noqa: E402


def build_pipeline(db, department_model, llm_client, scorer=None, default_confidence_threshold: float = 0.5):
    graph = StateGraph(TicketState)
    graph.add_node("extract", make_extract_node())
    graph.add_node("redact", make_redact_node())
    graph.add_node("classify", make_classify_node())
    graph.add_node("route", make_route_node(db, department_model))
    graph.add_node("retrieve", make_retrieve_node(db))
    graph.add_node("draft", make_draft_node(llm_client))
    graph.add_node("check", make_check_node(scorer))
    graph.add_node("signals", make_signals_node())
    graph.add_node("gate", make_gate_node(db))
    graph.add_node("score", make_score_node(db, department_model, default_confidence_threshold))
    graph.add_node("show", make_show_node())
    graph.add_node("escalate", make_escalate_node())

    graph.set_entry_point("extract")
    graph.add_edge("extract", "redact")
    graph.add_edge("redact", "classify")
    graph.add_edge("classify", "route")
    graph.add_edge("route", "retrieve")
    graph.add_edge("retrieve", "draft")
    graph.add_edge("draft", "check")
    graph.add_edge("check", "signals")
    graph.add_edge("signals", "gate")
    graph.add_edge("gate", "score")
    graph.add_conditional_edges("score", gate_condition, {"draft": "show", "escalate": "escalate"})
    graph.add_edge("show", END)
    graph.add_edge("escalate", END)

    return graph.compile()
