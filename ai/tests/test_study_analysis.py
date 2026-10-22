"""User-study analysis (H4): SUS scoring, paired time reduction, accepted major errors."""

import pytest

from study.analyse import analyse, summary_md, sus_score


def test_sus_score_matches_the_standard_formula():
    assert sus_score([5, 1, 5, 1, 5, 1, 5, 1, 5, 1]) == 100.0
    assert sus_score([1, 5, 1, 5, 1, 5, 1, 5, 1, 5]) == 0.0
    assert sus_score([3] * 10) == 50.0
    with pytest.raises(ValueError):
        sus_score([3] * 9)
    with pytest.raises(ValueError):
        sus_score([0] + [3] * 9)


def _tasks(participant, manual_ms, workbench_ms, workbench_actions=None):
    rows = []
    for i, ms in enumerate(manual_ms):
        rows.append({"task_id": f"{participant}-m{i}", "participant": participant, "condition": "manual",
                     "lane": "assisted", "action": "write", "time_ms": str(ms)})
    for i, ms in enumerate(workbench_ms):
        action = (workbench_actions or {}).get(i, "accept")
        rows.append({"task_id": f"{participant}-w{i}", "participant": participant, "condition": "workbench",
                     "lane": "escalate" if action == "escalate" else "assisted", "action": action,
                     "time_ms": str(ms)})
    return rows


def test_paired_reduction_major_errors_and_h4():
    tasks = (_tasks("P01", [100_000] * 4, [50_000] * 4, {3: "escalate"})
             + _tasks("P02", [80_000] * 4, [60_000] * 4))
    grades = {t["task_id"]: "A" for t in tasks if t["action"] != "escalate"}
    grades["P01-m0"] = "W"  # one major error, manual condition
    report = analyse(tasks, grades, {"P01": [4, 2] * 5, "P02": [5, 1] * 5})

    assert report["n_participants"] == 2
    p1 = report["per_participant"]["P01"]
    assert p1["time_reduction"] == 0.5 and p1["workbench"]["escalated"] == 1 and p1["workbench"]["sent"] == 3
    assert p1["manual"]["major_errors"] == 1 and p1["manual"]["major_error_rate"] == 0.25
    assert report["per_participant"]["P02"]["time_reduction"] == 0.25
    assert report["handling_time"]["median_reduction"] == 0.375
    assert report["major_errors"] == {**report["major_errors"], "manual": 1, "workbench": 0, "ungraded_replies": 0}
    assert report["sus"]["mean"] == 87.5
    assert report["H4"] == {**report["H4"], "time_target_met": True, "no_increase_in_major_errors": True}
    assert report["workbench_lane_actions"] == {"assisted:accept": 7, "escalate:escalate": 1}
    assert "| Median handling time (s) | 90.0 | 55.0 |" in summary_md(report)


def test_participant_with_one_condition_is_left_out():
    tasks = _tasks("P01", [100_000], [50_000]) + _tasks("P02", [100_000], [])
    assert analyse(tasks, {}, {})["n_participants"] == 1


def test_ungraded_replies_are_counted_not_guessed():
    tasks = _tasks("P01", [100_000] * 2, [50_000] * 2)
    report = analyse(tasks, {"P01-m0": "A"}, {})
    assert report["major_errors"]["ungraded_replies"] == 3
    assert report["per_participant"]["P01"]["workbench"]["major_error_rate"] is None
