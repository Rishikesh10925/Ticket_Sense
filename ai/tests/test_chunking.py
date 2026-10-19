import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "embeddings"))

from chunking import MAX_TOKENS, chunk_article, estimate_tokens  # noqa: E402

from benchmark.kb import load_articles  # noqa: E402
from benchmark.taxonomy import load_taxonomy  # noqa: E402


def test_every_v2_article_chunks_within_budget_and_never_indexes_key_facts():
    tax = load_taxonomy()
    for a in (a for a in load_articles() if a.is_v2):
        chunks = chunk_article(a.title, tax.topic(a.topic).name, a.sections)
        assert chunks, a.id
        for c in chunks:
            assert c.n_tokens <= MAX_TOKENS + 5, (a.id, c.n_tokens)
            assert c.text.startswith(a.title)
            assert "## Key facts" not in c.text
        covered = {s for c in chunks for s in c.sections}
        assert {"Symptom", "Resolution steps"} <= covered


def test_small_sections_are_packed_and_order_kept():
    sections = {"Symptom": "VPN hangs.", "Cause": "Port blocked.", "Resolution steps": "1. Try a hotspot.\n2. Retry."}
    chunks = chunk_article("VPN", "VPN connectivity", sections)
    assert len(chunks) == 1
    assert chunks[0].sections == ("Symptom", "Cause", "Resolution steps")
    text = chunks[0].text
    assert text.index("## Symptom") < text.index("## Cause") < text.index("## Resolution steps")


def test_long_resolution_is_split_at_steps():
    steps = "\n".join(f"{i}. " + "word " * 40 for i in range(1, 9))
    chunks = chunk_article("Long", None, {"Symptom": "x", "Resolution steps": steps}, max_tokens=120)
    assert len(chunks) > 2
    assert all(c.n_tokens <= 125 for c in chunks)
    assert all(estimate_tokens(c.text) == c.n_tokens for c in chunks)
