import asyncio
import json
import sys
import uuid
from pathlib import Path

AI_DIR = Path(__file__).resolve().parents[2] / "ai"
sys.path.insert(0, str(AI_DIR))

from generation.llm import ExtractiveStubClient, FakeLLMClient, LLMError  # noqa: E402
from graph.nodes import (  # noqa: E402
    gate_condition,
    lexical_scorer,
    make_check_node,
    make_classify_node,
    make_draft_node,
    make_escalate_node,
    make_extract_node,
    make_show_node,
    render_draft,
)
from graph.pipeline import build_pipeline  # noqa: E402

SAMPLES_DIR = Path(__file__).resolve().parents[2] / "data" / "sample_screenshots"

_PASSAGES = [
    {
        "n": 1,
        "article_id": str(uuid.uuid4()),
        "article_key": "NET-VPN-001",
        "chunk_id": str(uuid.uuid4()),
        "title": "VPN Client Not Connecting",
        "text": "Restart the VPN client and sign in again with your network account.",
    },
]


def test_extract_node_ocrs_image_attachment():
    node = make_extract_node()
    result = asyncio.run(
        node(
            {
                "attachment_path": str(SAMPLES_DIR / "networking_vpn_error.png"),
                "attachment_type": "image",
            }
        )
    )

    assert "VPN" in result["attachment_text"]
    assert result["ocr_confidence"] is not None


def test_extract_node_handles_no_attachment():
    node = make_extract_node()
    result = asyncio.run(node({"attachment_path": None, "attachment_type": None}))

    assert result == {"attachment_text": None, "ocr_confidence": None}


def test_classify_node_folds_in_attachment_text():
    # A vague subject/description paired with an on-topic attachment should still
    # classify sensibly once the attachment text is folded in — see
    # _augmented_description in graph/nodes.py.
    node = make_classify_node()
    result = asyncio.run(
        node(
            {
                "subject": "Issue",
                "description": "See attached.",
                "attachment_text": "VPN Connection Error. Error 619: the remote computer did not respond.",
            }
        )
    )
    assert result["department_name"]


def test_draft_node_returns_a_cited_structured_draft():
    node = make_draft_node(ExtractiveStubClient())
    result = asyncio.run(node({"subject": "VPN broken", "description": "Can't connect", "passages": _PASSAGES}))

    assert result["draft_result"]["schema_valid"] and result["draft_result"]["shown"]
    assert result["draft"].startswith("1. Restart the VPN client")
    assert result["draft"].endswith("[1]")
    assert result["citations"] == [
        {
            "n": 1,
            "source_type": "knowledge_base",
            "source_id": _PASSAGES[0]["article_id"],
            "article_key": "NET-VPN-001",
            "title": "VPN Client Not Connecting",
        }
    ]


def test_draft_node_without_evidence_is_not_shown():
    node = make_draft_node(ExtractiveStubClient())
    result = asyncio.run(node({"subject": "Odd request", "description": "Nothing matches", "passages": []}))

    assert result["draft_result"]["can_answer"] is False
    assert result["draft"] is None and result["citations"] == []


def test_draft_node_rejects_an_uncited_step():
    bad = json.dumps({"can_answer": True, "steps": [{"text": "Reboot.", "citations": []}], "missing_information": []})
    node = make_draft_node(FakeLLMClient(lambda r: bad))
    result = asyncio.run(node({"subject": "VPN", "description": "x", "passages": _PASSAGES}))

    assert result["draft_result"]["rejection"] == "step without citation"
    assert result["draft"] is None


def test_draft_node_survives_an_unreachable_model():
    def down(request):
        raise LLMError("connection refused")

    node = make_draft_node(FakeLLMClient(down))
    result = asyncio.run(node({"subject": "VPN", "description": "x", "passages": _PASSAGES}))

    assert result["draft_result"]["shown"] is False
    assert "model unavailable" in result["draft_result"]["rejection"]


def test_check_node_scores_each_claim_and_keeps_the_weakest():
    steps = [
        {"text": "Restart the VPN client.", "citations": [1]},
        {"text": "Open port 4433 on the corporate firewall.", "citations": [1]},
    ]
    node = make_check_node(lexical_scorer)
    result = asyncio.run(node({"draft_result": {"shown": True, "steps": steps}, "passages": _PASSAGES}))

    grounding = result["grounding"]
    supported, invented = (c["support"] for c in grounding["claims"])
    assert supported == 1.0 and invented < 0.5
    assert grounding["groundedness"] == 0.5
    assert grounding["weakest"][0]["text"].startswith("Open port 4433")


def test_check_node_skips_a_draft_that_is_not_shown():
    node = make_check_node(lexical_scorer)
    assert asyncio.run(node({"draft_result": {"shown": False}})) == {"grounding": None}


def test_render_draft_numbers_steps_and_keeps_citations():
    steps = [{"text": "A thing.", "citations": [1, 2]}, {"text": "B thing.", "citations": [3]}]
    assert render_draft(steps) == "1. A thing. [1][2]\n2. B thing. [3]"


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

    pipeline = build_pipeline(db=None, department_model=_FakeDepartment, llm_client=ExtractiveStubClient())
    assert pipeline is not None


def test_gate_condition_routes_to_draft_when_score_clears_threshold():
    assert gate_condition({"confidence_score": 0.7, "confidence_threshold": 0.5}) == "draft"
    assert gate_condition({"confidence_score": 0.5, "confidence_threshold": 0.5}) == "draft"  # exact tie passes


def test_gate_condition_routes_to_escalate_when_score_below_threshold():
    assert gate_condition({"confidence_score": 0.3, "confidence_threshold": 0.5}) == "escalate"


def test_gate_condition_fails_open_to_draft_on_missing_score():
    assert gate_condition({}) == "draft"


def test_escalate_node_returns_gate_decision():
    node = make_escalate_node()
    result = asyncio.run(node({}))
    assert result == {"gate_decision": "escalate"}


def test_gate_escalates_a_draft_that_is_not_shown_whatever_the_score():
    state = {"draft_result": {"shown": False}, "confidence_score": 0.99, "confidence_threshold": 0.5}
    assert gate_condition(state) == "escalate"


def test_show_node_reports_gate_decision():
    assert asyncio.run(make_show_node()({})) == {"gate_decision": "draft"}
