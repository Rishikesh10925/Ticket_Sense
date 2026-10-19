from judge.batch_judge import references


def test_references_follow_provenance_not_type_labels():
    refs = references("v1")
    import json
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    tickets = [json.loads(x) for x in (root / "data/benchmark/benchmark_v1.jsonl").read_text(encoding="utf-8").splitlines() if x]
    kinds = {t["type"]: set() for t in tickets}
    for t in tickets:
        kinds[t["type"]].add(refs[t["ticket_id"]].kind)
    assert kinds == {"A": {"served"}, "B": {"served"}, "C1": {"withheld"}, "C2": {"none"}}
    b = next(t for t in tickets if t["type"] == "B")
    assert refs[b["ticket_id"]].uncovered_question == b["uncovered_question"]
    a = next(t for t in tickets if t["type"] == "A")
    assert 3 <= len(refs[a["ticket_id"]].key_facts) <= 6 and refs[a["ticket_id"]].title
