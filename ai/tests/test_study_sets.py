from collections import Counter

from study.study_sets import DEPARTMENTS, MIX, build


def _tickets():
    out, splits = [], {}
    for i in range(2000):
        typ = ["A", "A", "B", "C1", "C2"][i % 5]
        t = {"ticket_id": f"T-{i:05d}", "group_id": f"G{i // 2}", "type": typ,
             "department": DEPARTMENTS[(i // 5) % 5], "subject": "s", "body": "b"}
        out.append(t)
        splits[t["ticket_id"]] = "unseen" if typ == "C1" else ("test" if i % 7 == 0 else "train")
    return out, splits


def test_sets_are_matched_disjoint_and_avoid_excluded_tickets():
    tickets, splits = _tickets()
    skip = {"T-00000", "T-00001", "T-00005"}
    a, b = build(tickets, splits, skip)
    assert len(a) == len(b) == sum(MIX.values()) == 20
    assert Counter(t["type"] for t in a) == Counter(t["type"] for t in b) == Counter(MIX)
    assert Counter(t["department"] for t in a) == Counter(t["department"] for t in b)
    ids = [t["ticket_id"] for t in a + b]
    assert len(set(ids)) == 40 and not set(ids) & skip
    assert all(splits[i] != "test" for i in ids)
    assert len({t["group_id"] for t in a + b}) == 40  # one paraphrase per scenario
