import numpy as np
import pytest

from grounding.consistency import consistency, pair_similarity, sample_seeds

VOCAB = ["hotspot", "restart", "firewall", "dns", "password"]


def _fake_embed(texts):
    # One-hot on the first vocabulary word found: identical topics -> cosine 1, else 0.
    out = np.zeros((len(texts), len(VOCAB) + 1))
    for i, t in enumerate(texts):
        hit = next((k for k, w in enumerate(VOCAB) if w in t.lower()), len(VOCAB))
        out[i, hit] = 1.0
    return out


def _draft(*claims, can_answer=True):
    return {"can_answer": can_answer, "steps": [{"text": c} for c in claims]}


def test_identical_samples_are_fully_consistent():
    main = _draft("Use a mobile hotspot to test.", "Restart the client.")
    c = consistency(main, [main, main, main], embedder=_fake_embed)
    assert c.answer_agreement == 1.0 and c.claim_agreement == pytest.approx(1.0)


def test_divergent_samples_score_lower():
    main = _draft("Use a mobile hotspot to test.", "Restart the client.")
    others = [_draft("Turn off the firewall now."), _draft("Change the DNS server."),
              _draft("Reset the password.", can_answer=False)]
    c = consistency(main, others, embedder=_fake_embed)
    assert c.claim_agreement < 0.2 and c.answer_agreement == pytest.approx(2 / 3, abs=1e-3)


def test_abstaining_main_draft_has_no_claim_agreement():
    c = consistency(_draft(can_answer=False), [_draft(can_answer=False)], embedder=_fake_embed)
    assert c.claim_agreement is None and c.answer_agreement == 1.0


def test_pair_similarity_edge_cases_and_seeds():
    empty = np.empty((0, 3))
    assert pair_similarity(empty, empty) == 1.0
    assert pair_similarity(np.eye(3)[:1], empty) == 0.0
    assert sample_seeds(7) == [701, 702, 703] and len(set(sample_seeds(7, 5))) == 5
    with pytest.raises(ValueError):
        consistency(_draft("x"), [])
