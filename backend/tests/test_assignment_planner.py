from collections import Counter, defaultdict

import pytest

from app.services.assignments import choose_overlap, plan_adjudications, plan_assignments

STRATA = ["A|SAP", "A|HR", "B|Cloud", "C1|Database", "C2|Networking"]
DRAFTS = [(f"d{i:03d}", STRATA[i % len(STRATA)]) for i in range(600)]
REVIEWERS = [f"REV-{i:02d}" for i in range(1, 7)]


def _plan(seed=7):
    return plan_assignments(DRAFTS, REVIEWERS, n_overlap=150, seed=seed)


def test_overlap_drafts_get_two_different_reviewers_and_others_one():
    by_draft = defaultdict(list)
    for a in _plan():
        by_draft[a.draft_id].append(a)
    counts = Counter(len(v) for v in by_draft.values())
    assert counts == {1: 450, 2: 150}
    for items in by_draft.values():
        assert len({a.annotator_id for a in items}) == len(items)
        assert all(a.overlap == (len(items) == 2) for a in items)


def test_loads_are_balanced_within_one_item():
    loads = Counter(a.annotator_id for a in _plan())
    assert sum(loads.values()) == 750
    assert max(loads.values()) - min(loads.values()) <= 1


def test_each_reviewer_gets_a_shuffled_permutation_of_positions():
    by_reviewer = defaultdict(list)
    for a in _plan():
        by_reviewer[a.annotator_id].append(a)
    for items in by_reviewer.values():
        assert sorted(a.position for a in items) == list(range(1, len(items) + 1))
        in_order = [a.draft_id for a in sorted(items, key=lambda a: a.position)]
        assert in_order != sorted(in_order)  # not simply id order


def test_overlap_set_is_spread_over_strata():
    import random

    chosen = choose_overlap(DRAFTS, 150, random.Random(1))
    per_stratum = Counter(dict(DRAFTS)[d] for d in chosen)
    assert set(per_stratum.values()) == {30}


def test_same_seed_same_plan_and_different_seed_different_order():
    assert _plan(7) == _plan(7)
    assert _plan(7) != _plan(8)


def test_double_annotation_needs_two_reviewers():
    with pytest.raises(ValueError):
        plan_assignments(DRAFTS[:10], ["REV-01"], n_overlap=2, seed=1)


def test_adjudication_goes_to_a_third_reviewer_after_their_queue():
    plan = plan_adjudications(
        [("d001", ["REV-01", "REV-02"]), ("d002", ["REV-01", "REV-03"])],
        ["REV-01", "REV-02", "REV-03"],
        current_load={"REV-01": 100, "REV-02": 100, "REV-03": 100},
        next_position={"REV-01": 101, "REV-02": 101, "REV-03": 101},
        seed=3,
    )
    assert [(a.draft_id, a.annotator_id, a.position) for a in plan] == [("d001", "REV-03", 101), ("d002", "REV-02", 101)]
