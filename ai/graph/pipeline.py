"""Builds and compiles the classify -> route -> retrieve -> draft LangGraph
StateGraph for a single ticket. See docs/langgraph-pipeline.md for the design and
docs/langgraph-research.md (Week 1) for the original target shape this implements
(the confidence-scoring node and gate sketched there are out of scope for this week).

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

from graph.nodes import make_classify_node, make_draft_node, make_retrieve_node, make_route_node  # noqa: E402
from graph.state import TicketState  # noqa: E402


def build_pipeline(db, department_model, llm_provider):
    graph = StateGraph(TicketState)
    graph.add_node("classify", make_classify_node())
    graph.add_node("route", make_route_node(db, department_model))
    graph.add_node("retrieve", make_retrieve_node(db))
    graph.add_node("draft", make_draft_node(llm_provider))

    graph.set_entry_point("classify")
    graph.add_edge("classify", "route")
    graph.add_edge("route", "retrieve")
    graph.add_edge("retrieve", "draft")
    graph.add_edge("draft", END)

    return graph.compile()
