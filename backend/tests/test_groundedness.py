import sys
import uuid
from pathlib import Path

AI_EMBEDDINGS_DIR = Path(__file__).resolve().parents[2] / "ai" / "embeddings"
AI_GENERATION_DIR = Path(__file__).resolve().parents[2] / "ai" / "generation"
sys.path.insert(0, str(AI_EMBEDDINGS_DIR))
sys.path.insert(0, str(AI_GENERATION_DIR))

from retrieve import EvidenceResult  # noqa: E402
from groundedness import check_groundedness  # noqa: E402
from llm_interface import StubLLMProvider  # noqa: E402
from prompt import build_prompt  # noqa: E402

_EVIDENCE = [
    EvidenceResult("knowledge_base", uuid.uuid4(), "Article A", "content a", uuid.uuid4(), 0.1),
    EvidenceResult("knowledge_base", uuid.uuid4(), "Article B", "content b", uuid.uuid4(), 0.2),
]


def test_flags_out_of_range_citation():
    draft = "- A real claim [1]\n- A fabricated claim [3]"
    report = check_groundedness(draft, _EVIDENCE)
    assert report.ungrounded_markers == [3]
    assert not report.is_fully_grounded


def test_flags_uncited_line():
    draft = "- A cited claim [1]\n- An uncited claim with no marker at all"
    report = check_groundedness(draft, _EVIDENCE)
    assert len(report.uncited_lines) == 1
    assert not report.is_fully_grounded


def test_passes_fully_grounded_draft():
    draft = "- Claim from A [1]\n- Claim from B [2]"
    report = check_groundedness(draft, _EVIDENCE)
    assert report.is_fully_grounded
    assert report.grounded_citations == 2


def test_stub_provider_produces_grounded_output():
    evidence = [
        EvidenceResult(
            "knowledge_base",
            uuid.uuid4(),
            "VPN Client Not Connecting",
            "# VPN Client Not Connecting\n\n## Resolution\n1. Restart the VPN client. 2. Retry.",
            uuid.uuid4(),
            0.1,
        )
    ]
    prompt = build_prompt("VPN broken", "Cannot connect", evidence)
    draft = StubLLMProvider().generate(prompt, evidence)
    report = check_groundedness(draft, evidence)
    assert report.is_fully_grounded
    assert "[1]" in draft


def test_stub_provider_handles_no_evidence():
    draft = StubLLMProvider().generate("irrelevant prompt", [])
    assert "escalat" in draft.lower()
    report = check_groundedness(draft, [])
    assert report.total_citations == 0
