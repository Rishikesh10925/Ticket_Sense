from confidence_model.dataset import Row
from confidence_model.shift import MAX_COST, choose_guard, outcome, split_topics
from gate.service import Thresholds


def _row(topic, prob, margin, acceptable, split="unseen"):
    return Row("d", "t", "g", "C1", "SAP", topic, split, True,
               {"rt_dept_max_prob": prob, "rt_probe_margin": margin}, acceptable)


def test_topic_split_is_seeded_and_disjoint():
    topics = ["a", "b", "c", "d", "e", "f"]
    tune, held = split_topics(topics)
    assert split_topics(topics) == (tune, held)
    assert len(tune) == len(held) == 3 and not set(tune) & set(held)


def test_guard_blocks_unsure_unseen_drafts_within_the_cost_budget():
    base = Thresholds("t", None, 0.0)
    unseen = [_row("x", 0.3, 0.2, 0)] * 8 + [_row("x", 0.95, 0.3, 0)] * 2
    val = [_row("k", 0.95, 0.3, 1, "val")] * 18 + [_row("k", 0.4, 0.3, 1, "val")] * 2
    best, trials = choose_guard(unseen, [0.9] * 10, val, [0.9] * 20, base)
    assert best["val_cost"] <= MAX_COST and best["tune_unacceptable_blocked"] == 0.8
    assert all(t["val_cost"] <= MAX_COST or t is not best for t in trials)


def test_outcome_counts_what_the_guard_changes():
    base = Thresholds("t", None, 0.0)
    guard = Thresholds("t", None, 0.0, min_dept_prob=0.5)
    rows = [_row("x", 0.3, 0.2, 0), _row("x", 0.9, 0.2, 1)]
    o = outcome(rows, [0.9, 0.9], guard, base)
    assert (o["shown_without_guard"], o["shown_with_guard"]) == (2, 1)
    assert o["unacceptable_blocked_share"] == 1.0 and o["acceptable_blocked_share"] == 0.0
