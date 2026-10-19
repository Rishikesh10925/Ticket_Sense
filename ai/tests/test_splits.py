import random

from benchmark.splits import assign_splits, check_manifest, leakage_group


def _records(n_articles=60, per_article=6, n_c1_articles=12, n_c2_groups=20):
    rng = random.Random(0)
    depts = ["SAP", "Networking", "Cloud", "Database", "HR"]
    out, tid = [], 0
    for a in range(n_articles):
        t = "A" if a % 5 else "B"
        for k in range(per_article):
            tid += 1
            out.append({"ticket_id": f"T{tid}", "group_id": f"G{a}-{k // 3}", "type": t,
                        "department": depts[a % 5], "gold_articles": [f"ART-{a}"]})
    for a in range(n_c1_articles):
        for k in range(per_article):
            tid += 1
            out.append({"ticket_id": f"T{tid}", "group_id": f"H{a}", "type": "C1",
                        "department": depts[a % 5], "gold_articles": [f"W-{a}"]})
    for g in range(n_c2_groups):
        for k in range(3):
            tid += 1
            out.append({"ticket_id": f"T{tid}", "group_id": f"V{g}", "type": "C2",
                        "department": rng.choice(depts), "gold_articles": []})
    return out


def test_no_leakage_and_c1_only_in_test_or_unseen():
    records = _records()
    assignment = assign_splits(records)
    assert check_manifest(records, assignment) == []
    assert {assignment[r["ticket_id"]] for r in records if r["type"] == "C1"} <= {"test", "unseen"}


def test_split_sizes_are_near_targets():
    records = _records()
    assignment = assign_splits(records)
    seen = [r for r in records if r["type"] != "C1"]
    share = sum(assignment[r["ticket_id"]] == "train" for r in seen) / len(seen)
    assert 0.48 < share < 0.68
    for split in ("val", "calib", "test"):
        assert any(assignment[r["ticket_id"]] == split for r in seen)


def test_deterministic_and_seed_sensitive():
    records = _records()
    assert assign_splits(records, 1) == assign_splits(records, 1)
    assert assign_splits(records, 1) != assign_splits(records, 2)


def test_check_manifest_catches_leakage():
    records = _records(n_articles=5, n_c1_articles=1, n_c2_groups=1)
    assignment = assign_splits(records)
    a, b = [r for r in records if leakage_group(r) == "ART:ART-0"][:2]
    assignment[b["ticket_id"]] = "val" if assignment[a["ticket_id"]] != "val" else "train"
    assert any("spans" in p for p in check_manifest(records, assignment))
