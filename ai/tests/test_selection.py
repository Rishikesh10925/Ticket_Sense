from collections import Counter

from signals.select_for_labelling import allocate, select


def _tickets():
    out = []
    for i in range(1000):
        split = ["train", "val", "calib", "test", "unseen"][i % 5]
        out.append({"ticket_id": f"T-{i:05d}", "split": split, "type": ["A", "A", "B", "C1", "C2"][i % 7 % 5],
                    "department": ["SAP", "HR", "Cloud", "Database", "Networking"][i % 3]})
    return out


def test_allocation_is_proportional_and_exact():
    alloc = allocate({"a": 50, "b": 30, "c": 20}, 10)
    assert alloc == {"a": 5, "b": 3, "c": 2} and sum(allocate({"a": 7, "b": 7, "c": 7}, 10).values()) == 10
    assert allocate({"a": 3}, 10) == {"a": 3}  # capped at the cell size


def test_quotas_are_met_and_unseen_is_never_selected():
    sel = select(_tickets(), quotas={"test": 150, "calib": 120, "train+val": 90})
    sizes = {k: len(v) for k, v in sel["selected"].items()}
    assert sizes == {"test": 150, "calib": 120, "train+val": 90}
    by_id = {t["ticket_id"]: t for t in _tickets()}
    assert {by_id[i]["split"] for i in sel["selected"]["test"]} == {"test"}
    assert not any(by_id[i]["split"] == "unseen" for ids in sel["selected"].values() for i in ids)


def test_strata_shares_follow_the_split():
    tickets = _tickets()
    sel = select(tickets, quotas={"test": 100, "calib": 100, "train+val": 100})
    pool = [t for t in tickets if t["split"] == "test"]
    want = Counter(t["type"] for t in pool)
    got = Counter(next(t for t in tickets if t["ticket_id"] == i)["type"] for i in sel["selected"]["test"])
    for typ, n in want.items():
        assert abs(got[typ] - 100 * n / len(pool)) <= 3


def test_same_seed_same_selection():
    assert select(_tickets()) == select(_tickets())
    assert select(_tickets(), seed=1) != select(_tickets(), seed=2)
