import zipfile

import pytest
from evaluation.human_audit import allocate_random, analyse, check_rating, flags, outcome_status, read_xlsx, select, split_into_pairs


def draft(i, group, type_="A", support=(0.9,), judge="M"):
    return {"draft_id": f"d{i}", "group_id": group, "type": type_, "judge": judge,
            "claims": [{"support": s} for s in support]}


def rating(q1="A", q2="Fully", q3="Yes", reason="", seconds="100"):
    return {"q1": q1, "q2": q2, "q3": q3, "reason": reason, "seconds": seconds}


def test_allocation_is_equal_when_it_can_be_and_capped_when_not():
    assert allocate_random(24, {"A": 30, "B": 30, "C1": 30, "C2": 30}) == {"A": 6, "B": 6, "C1": 6, "C2": 6}
    assert allocate_random(24, {"A": 30, "B": 9, "C1": 69, "C2": 2}) == {"A": 7, "B": 7, "C1": 8, "C2": 2}
    with pytest.raises(ValueError):
        allocate_random(10, {"A": 3, "B": 3})


def test_flags_follow_the_protocol_rules():
    assert flags(draft(1, "g", support=(0.6, 0.5), judge="R"), {})["nli_pass_suspected_error"]
    assert not flags(draft(1, "g", support=(0.6, 0.4), judge="R"), {})["nli_pass_suspected_error"]
    assert flags(draft(1, "g", support=(0.4,)), {})["nli_rejected"]
    assert flags(draft(1, "g", judge="M"), {"d1": "R"})["judge_disagreement"]
    assert not flags(draft(1, "g", judge="M"), {"d1": "A"})["judge_disagreement"]  # a change within A/M does not count


def pool():
    out = []
    for g in range(40):
        kind = g % 4
        out += [draft(f"{g}x{k}", f"G{g}", ("A", "B", "C1", "C2")[g % 4] if g < 30 else "C1",
                      support={0: (0.9,), 1: (0.2,), 2: (0.9,), 3: (0.2,)}[kind], judge={0: "R", 1: "M", 2: "M", 3: "W"}[kind])
                for k in range(2)]
    return out


def test_selection_has_one_draft_per_scenario_and_is_reproducible():
    blind = {d["draft_id"]: "R" for d in pool() if d["judge"] == "M"}
    a = select(pool(), blind, 20, seed=7)
    assert [c["draft_id"] for c in a["cases"]] == [c["draft_id"] for c in select(pool(), blind, 20, seed=7)["cases"]]
    assert len(a["cases"]) == 20 and len({c["group_id"] for c in a["cases"]}) == 20
    assert sum(c["part"] == "I" for c in a["cases"]) == 12


def test_selection_refuses_an_impossible_quota_and_mixed_scenarios():
    with pytest.raises(ValueError, match="qualify"):
        select(pool(), {}, 20, seed=7)  # no blind verdicts, so no judge disagreements
    with pytest.raises(ValueError, match="more than one type"):
        select([draft(1, "G", "A"), draft(2, "G", "B")], {}, 20, seed=7)


def test_pairs_split_everything_once():
    cases = [{"draft_id": str(i), "group": str(i % 3)} for i in range(21)]
    parts = split_into_pairs(cases, 2, seed=1)
    assert sorted(c["draft_id"] for p in parts for c in p) == sorted(c["draft_id"] for c in cases)
    assert abs(len(parts[0]) - len(parts[1])) <= 1


def test_reason_is_required_only_where_the_protocol_says():
    assert check_rating(rating()) == []
    assert check_rating(rating(q1="R")) == ["a reason is required"]
    assert check_rating(rating(q3="No", reason="other problem")) == []
    assert check_rating(rating(q1="X"))


def test_a_finding_needs_both_reviewers():
    from evaluation.human_audit import _supported_unacceptable as rule
    yes, no, unsure = rating(q1="W"), rating(q1="A"), rating(q1="U")
    assert outcome_status([yes, yes], rule) == "confirmed"
    assert outcome_status([no, no], rule) == "negative"
    assert outcome_status([yes, no], rule) == "unresolved"
    assert outcome_status([yes, unsure], rule) == "unresolved"
    assert outcome_status([yes], rule) == "incomplete"
    assert outcome_status([yes, no], rule, third=yes) == "confirmed_adjudicated"
    assert outcome_status([yes, no], rule, third=unsure) == "unresolved"


def test_analysis_keeps_denominators_and_weights_by_eligible_scenarios():
    cases = [{"draft_id": "a", "part": "I", "group": "random_A", "type": "A"},
             {"draft_id": "b", "part": "I", "group": "random_C1", "type": "C1"},
             {"draft_id": "c", "part": "II", "group": "judge_disagreement", "type": "C1"}]
    ratings = {"X": {"a": rating(q1="W"), "b": rating(q1="W"), "c": rating(q1="W")},
               "Y": {"a": rating(q1="W"), "b": rating(q1="A", seconds="5"), "c": rating(q1="W")}}
    pairs = {k: ["X", "Y"] for k in "abc"}
    r = analyse(cases, ratings, pairs, {"A": 30, "C1": 90})
    out = r["outcomes"]["supported_but_unacceptable"]
    # type A confirmed (share 0.25); type C1 disputed (share 0.75), so it only widens the upper bound
    assert out["part_I_weighted_bounds"] == [0.25, 1.0]
    assert out["counts"]["II/judge_disagreement"] == {"confirmed": 1, "selected": 1}
    assert r["disputed_binary"] == ["b"]
    assert r["reviewers"]["Y"]["under_quick_limit"] == 1
    assert r["pairs"]["X+Y"]["double_rated"] == 3


def test_read_xlsx_handles_inline_and_shared_strings(tmp_path):
    main = 'xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"'
    rels = 'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"'
    path = tmp_path / "x.xlsx"
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("xl/workbook.xml", f'<workbook {main} {rels}><sheets><sheet name="Ratings" sheetId="1" r:id="rId1"/></sheets></workbook>')
        z.writestr("xl/_rels/workbook.xml.rels", '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                   '<Relationship Id="rId1" Type="w" Target="worksheets/sheet1.xml"/></Relationships>')
        z.writestr("xl/sharedStrings.xml", f"<sst {main}><si><t>q1</t></si><si><t>W</t></si></sst>")
        z.writestr("xl/worksheets/sheet1.xml", f'<worksheet {main}><sheetData>'
                   '<row r="1"><c r="A1" t="s"><v>0</v></c><c r="B1" t="inlineStr"><is><t>seconds</t></is></c></row>'
                   '<row r="2"><c r="A2" t="s"><v>1</v></c><c r="B2"><v>12</v></c></row></sheetData></worksheet>')
    assert read_xlsx(path) == {"Ratings": [{"q1": "W", "seconds": "12"}]}
