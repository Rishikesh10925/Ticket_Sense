import copy
import json
from pathlib import Path

from benchmark.kb import load_articles
from benchmark.validate_benchmark import validate

ROOT = Path(__file__).resolve().parents[2]
TICKETS = [json.loads(x) for x in (ROOT / "data/benchmark/tickets_v0.jsonl").read_text(encoding="utf-8").splitlines()]
MANIFEST = json.loads((ROOT / "data/benchmark/splits_v0.json").read_text(encoding="utf-8"))
ARTICLES = load_articles()


def _first(t):
    return next(i for i, r in enumerate(TICKETS) if r["type"] == t)


def test_committed_sample_is_green():
    assert validate(TICKETS, ARTICLES, MANIFEST, ROOT / "data/benchmark/tickets_v0.jsonl") == []


def test_catches_missing_gold_article_and_withheld_misuse():
    recs = copy.deepcopy(TICKETS)
    recs[_first("A")]["gold_articles"] = ["SAP-XX-999"]
    recs[_first("C1")]["gold_articles"] = ["SAP-ACC-001"]  # served article used for a C1 ticket
    problems = " ".join(validate(recs, ARTICLES, None, None))
    assert "does not exist" in problems and "C1 ticket built on served article" in problems


def test_catches_split_leakage_and_hash_mismatch(tmp_path):
    manifest = copy.deepcopy(MANIFEST)
    c1 = TICKETS[_first("C1")]["ticket_id"]
    manifest["assignment"][c1] = "train"
    other = tmp_path / "other.jsonl"
    other.write_text("{}", encoding="utf-8")
    problems = " ".join(validate(TICKETS, ARTICLES, manifest, other))
    assert "is C1 but in train" in problems and "hash does not match" in problems


def test_catches_duplicates_and_type_drift():
    recs = copy.deepcopy(TICKETS) + [dict(TICKETS[0], ticket_id="T-99999")] * 30
    problems = " ".join(validate(recs, ARTICLES, None, None))
    assert "duplicate another ticket" in problems and "type A is" in problems
