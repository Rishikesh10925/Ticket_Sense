import math

from generation.drafting import Passage
from generation.llm import FakeLLMClient
from signals.model_side import token_probability, verbalised_confidence

PASSAGES = [Passage(1, "VPN", "Restart the VPN client.")]
STEPS = [{"text": "Restart the VPN client.", "citations": [1]}]


def test_token_probability_summaries():
    out = token_probability([-0.1, -0.5, -2.0])
    assert out["b2_min_logprob"] == -2.0
    assert out["b2_mean_logprob"] == round(-2.6 / 3, 4)
    assert out["b2_mean_prob"] == round(math.exp(-2.6 / 3), 4)
    assert token_probability(None) == {"b2_mean_logprob": None, "b2_min_logprob": None, "b2_mean_prob": None}


def test_verbalised_confidence_scales_and_sees_the_draft():
    seen = []

    def respond(req):
        seen.append(req.user)
        return '{"confidence": 85}'

    assert verbalised_confidence(FakeLLMClient(respond), "VPN broken", None, PASSAGES, STEPS, True) == 0.85
    assert "<draft can_answer=\"True\">" in seen[0] and "Restart the VPN client." in seen[0]
    assert "Draft the reply now" not in seen[0]


def test_verbalised_confidence_tolerates_bad_output():
    assert verbalised_confidence(FakeLLMClient(lambda r: "sure!"), "x", None, PASSAGES, STEPS, True) is None
    assert verbalised_confidence(FakeLLMClient(lambda r: '{"confidence": 140}'), "x", None, PASSAGES, STEPS, True) == 1.0
