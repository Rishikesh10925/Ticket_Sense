from benchmark.freeze import verify


def test_frozen_benchmark_v1_is_unchanged():
    # Any edit to a frozen ticket, the split manifest, the taxonomy or a KB article
    # must go through a refreeze and a pre-registration amendment.
    assert verify("v1") == []


def test_recording_a_reviewer_does_not_change_the_article_hash(tmp_path):
    from benchmark.freeze import article_sha256

    a, b, c = tmp_path / "a.md", tmp_path / "b.md", tmp_path / "c.md"
    a.write_text("---\nid: X\nreviewer: null\n---\nRestart the client.\n")
    b.write_text("---\nid: X\nreviewer: A\n---\nRestart the client.\n")
    c.write_text("---\nid: X\nreviewer: A\n---\nReinstall the client.\n")
    assert article_sha256(a) == article_sha256(b) != article_sha256(c)
