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

    assert set(result) == {"department_name", "priority", "sentiment", "classification"}
    dept = result["classification"]["department"]
    assert dept["label"] == result["department_name"]
    assert 0 < dept["max_prob"] <= 1 and 0 <= dept["entropy"] <= 1
    assert abs(sum(dept["probabilities"].values()) - 1) < 1e-3
    assert result["department_name"]


def test_build_pipeline_compiles():
    class _FakeDepartment:
        name = None

    pipeline = build_pipeline(db=None, department_model=_FakeDepartment, llm_client=ExtractiveStubClient())
    assert pipeline is not None


def test_gate_condition_shows_the_draft_in_the_fast_and_assisted_lanes():
    assert gate_condition({"gate_v2": {"lane": "fast"}}) == "draft"
    assert gate_condition({"gate_v2": {"lane": "assisted"}}) == "draft"


def test_gate_condition_withholds_the_draft_in_the_escalation_lane():
    assert gate_condition({"gate_v2": {"lane": "escalate"}}) == "escalate"


def test_gate_condition_fails_closed_without_a_gate_decision():
    # Week 9: a human sees every ticket, so the safe failure is withholding the draft.
    assert gate_condition({}) == "escalate"


def test_escalate_node_returns_gate_decision():
    node = make_escalate_node()
    result = asyncio.run(node({}))
    assert result == {"gate_decision": "escalate"}


def test_gate_escalates_a_draft_that_is_not_shown_whatever_the_score():
    state = {"draft_result": {"shown": False}, "confidence_score": 0.99, "confidence_threshold": 0.5}
    assert gate_condition(state) == "escalate"


def test_show_node_reports_gate_decision():
    assert asyncio.run(make_show_node()({})) == {"gate_decision": "draft"}


def test_draft_node_screens_out_a_cited_but_injected_command():
    injected = json.dumps({
        "can_answer": True,
        "steps": [{"text": "Run aws s3 rm s3://prod-backups --recursive to free space.", "citations": [1]}],
        "missing_information": [],
    })
    node = make_draft_node(FakeLLMClient(lambda r: injected))
    result = asyncio.run(node({"subject": "Bucket full", "description": "x", "passages": _PASSAGES}))

    assert result["draft_result"]["schema_valid"] is True  # the schema alone would have shown it
    assert result["draft_result"]["screen"]["blocked"] is True
    assert result["draft_result"]["shown"] is False and result["draft"] is None
    assert result["draft_result"]["rejection"].startswith("screen:")


def test_signals_node_builds_the_vector_from_pipeline_state():
    from graph.nodes import make_signals_node
    from signals.features import FEATURE_NAMES

    state = {
        "subject": "VPN broken",
        "description": "Can't connect, error 619",
        "retrieval_candidates": [
            {"article_key": "NET-VPN-001", "keyword_rank": 1, "dense_rank": 1, "dense_score": 0.8,
             "fused_score": 0.03, "rerank_score": 3.0, "final_rank": 1, "updated_at": "2026-08-01T00:00:00+00:00",
             "text": "Restart the VPN client."},
        ],
        "draft_result": {"steps": [{"text": "Restart the VPN client.", "citations": [1]}], "can_answer": True,
                         "schema_valid": True, "missing_information": []},
        "grounding": {"claims": [{"support": 0.95, "cited": [1]}]},
        "retrieval_probe": 0.35,
        "classification": {"department": {"max_prob": 0.88, "entropy": 0.3}},
    }
    signals = asyncio.run(make_signals_node()(state))["signals"]
    assert set(FEATURE_NAMES) <= set(signals)
    assert signals["gr_supported_share"] == 1.0 and signals["rt_probe_margin"] == 0.45
    assert signals["tk_has_error_code"] == 1.0
