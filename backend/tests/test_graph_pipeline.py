import asyncio
import sys
import uuid
from pathlib import Path

AI_DIR = Path(__file__).resolve().parents[2] / "ai"
sys.path.insert(0, str(AI_DIR))

from embeddings.retrieve import EvidenceResult  # noqa: E402
from generation.llm_interface import StubLLMProvider  # noqa: E402
from graph.nodes import make_classify_node, make_draft_node  # noqa: E402
from graph.pipeline import build_pipeline  # noqa: E402

_EVIDENCE = [
    EvidenceResult(
        "knowledge_base", uuid.uuid4(), "VPN Client Not Connecting",
        "# VPN Client Not Connecting\n\n## Resolution\nRestart the VPN client.",
        uuid.uuid4(), 0.1,
    ),
]


def test_draft_node_extracts_citations_from_generated_markers():
    node = make_draft_node(StubLLMProvider())
    result = asyncio.run(
        node({"subject": "VPN broken", "description": "Can't connect", "evidence": _EVIDENCE})
    )

    assert "[1]" in result["draft"]
    assert result["citations"] == [
        {
            "source_type": "knowledge_base",
            "source_id": str(_EVIDENCE[0].source_id),
            "title": "VPN Client Not Connecting",
        }
    ]


def test_draft_node_handles_no_evidence():
    node = make_draft_node(StubLLMProvider())
    result = asyncio.run(
        node({"subject": "Odd request", "description": "Nothing matches", "evidence": []})
    )

    assert result["citations"] == []
    assert "escalat" in result["draft"].lower()


def test_classify_node_returns_prediction_fields():
    node = make_classify_node()
    result = asyncio.run(
        node({"subject": "VPN not connecting from home", "description": "Client hangs on connect"})
    )

    assert set(result) == {"department_name", "priority", "sentiment"}
    assert result["department_name"]


def test_build_pipeline_compiles():
    class _FakeDepartment:
        name = None

    pipeline = build_pipeline(db=None, department_model=_FakeDepartment, llm_provider=StubLLMProvider())
    assert pipeline is not None
