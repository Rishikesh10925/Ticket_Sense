from benchmark.kb import SECTIONS, load_articles, parse_article, validate_article
from benchmark.taxonomy import load_taxonomy


def test_every_v2_article_follows_the_template():
    tax = load_taxonomy()
    problems = [p for a in load_articles() if a.is_v2 for p in validate_article(a, tax)]
    assert problems == []


def test_article_ids_are_unique():
    ids = [a.id for a in load_articles() if a.is_v2]
    assert len(ids) == len(set(ids))


def test_parse_v2_article(tmp_path):
    path = tmp_path / "NET-VPN-009.md"
    path.write_text(
        "---\nid: NET-VPN-009\ndepartment: Networking\ntopic: net-vpn\ntitle: T\n"
        "updated: 2026-01-02\nserved: true\nauthor: R\nreviewer: null\n---\n\n"
        "## Symptom\nS\n\n## Cause\nC\n\n## Resolution steps\n1. One.\n2. Two\n   continued.\n\n"
        "## Warnings\nW\n\n## Key facts\n- Fact one.\n- Fact two.\n- Fact three.\n",
        encoding="utf-8",
    )
    a = parse_article(path)
    assert a.is_v2 and a.id == "NET-VPN-009" and a.title == "T"
    assert list(a.sections) == list(SECTIONS)
    assert a.steps == ["One.", "Two continued."]
    assert a.key_facts == ["Fact one.", "Fact two.", "Fact three."]
    assert a.updated.isoformat() == "2026-01-02"
    # Key facts exist for the judge and are never indexed for retrieval.
    assert "Fact one" not in a.retrieval_text() and "## Cause" in a.retrieval_text()


def test_v1_article_still_parses(tmp_path):
    path = tmp_path / "old.md"
    path.write_text("# Old Title\n\n**Department:** HR\n\n## Issue\nx\n", encoding="utf-8")
    a = parse_article(path)
    assert not a.is_v2 and a.title == "Old Title" and a.retrieval_text().startswith("# Old Title")


def test_only_a_second_team_member_counts_as_human_review():
    from pathlib import Path

    from benchmark.kb import Article, is_human_reviewed

    def art(author, reviewer):
        a = Article(path=Path("x.md"), title="t", body="", meta={"id": "X", "author": author, "reviewer": reviewer})
        return a

    assert is_human_reviewed(art("S", "R"))
    assert not is_human_reviewed(art("S", "S"))  # the author cannot review their own article
    assert not is_human_reviewed(art("S", "Claude"))  # an AI fact-check is recorded, not counted
    assert not is_human_reviewed(art("S", None))
