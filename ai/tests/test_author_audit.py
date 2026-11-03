from evaluation.author_audit import Q1_ORDER, alpha, analyse, check_rating, outcome_status, _grounded_unacceptable


def rating(q1="A", q2="Fully", q3="Yes", reason="", seconds="100"):
    return {"q1": q1, "q2": q2, "q3": q3, "reason": reason, "seconds": seconds}


def test_alpha_matches_a_hand_computed_example():
    # coincidences: o11=2, o12=o21=1, o22=4; n=8, Do=2/8, De=2*3*5/(8*7) -> 1 - 0.25/0.5357
    units = [["1", "1"], ["1", "2"], ["2", "2"], ["2", "2"]]
    assert alpha(units, ("1", "2"), ordinal=False) == 0.5333
    assert alpha([["A", "A", "A"], ["W", "W", "W"]], Q1_ORDER, ordinal=True) == 1.0


def test_alpha_ignores_missing_values_and_is_undefined_without_variation():
    assert alpha([["A", "A", None], ["W", None, "W"], [None, None, "M"]], Q1_ORDER, ordinal=True) == 1.0
    assert alpha([["A", "A", "A"]], Q1_ORDER, ordinal=True) is None


def test_ordinal_alpha_counts_near_misses_as_smaller_disagreements():
    near = [["A", "M"], ["R", "R"], ["W", "W"], ["A", "A"]]
    far = [["A", "W"], ["R", "R"], ["M", "M"], ["A", "A"]]
    assert alpha(near, Q1_ORDER, ordinal=True) > alpha(far, Q1_ORDER, ordinal=True)


def test_reason_rule_follows_author_v2():
    assert check_rating(rating()) == []
    assert check_rating(rating(q2="Partially")) == ["a reason is required"]
    assert check_rating(rating(q1="M", q3="No")) == ["a reason is required"]
    assert check_rating(rating(q1="X"))


def test_findings_need_all_three_original_ratings():
    yes, no, unsure = rating(q1="W"), rating(q1="A"), rating(q1="U")
    rule = _grounded_unacceptable
    assert outcome_status([yes, yes, yes], rule) == "unanimous_positive"
    assert outcome_status([no, no, no], rule) == "unanimous_negative"
    assert outcome_status([yes, yes, no], rule) == "majority_positive"
    assert outcome_status([yes, unsure, no], rule) == "unresolved"
    assert outcome_status([yes, yes], rule) == "incomplete"


def test_analysis_reports_denominators_and_weights_part_one():
    cases = [{"draft_id": "a", "part": "I", "group": "random_A", "type": "A"},
             {"draft_id": "b", "part": "I", "group": "random_C1", "type": "C1"},
             {"draft_id": "c", "part": "II", "group": "judge_disagreement", "type": "C1"}]
    w, a = rating(q1="W"), rating(q1="A")
    ratings = {"R": {"a": w, "b": w, "c": w}, "S": {"a": w, "b": a, "c": w}, "T": {"a": w, "b": w}}
    r = analyse(cases, ratings, {"A": 30, "C1": 90}, seed=1)
    assert r["complete"] == 2 and r["selected"] == 3
    out = r["outcomes"]["grounded_but_unacceptable"]
    assert out["unanimous_cases"] == ["a"]
    assert out["part_I_weighted_bounds"] == [0.25, 1.0]
    assert out["counts"]["II/judge_disagreement"] == {"incomplete": 1, "selected": 1}
    assert r["disagreements"]["q1_binary"] == ["b"]
    assert r["agreement"]["q1_binary"]["all_agree"] == 1 and r["agreement"]["q1_binary"]["two_of_three"] == 1
