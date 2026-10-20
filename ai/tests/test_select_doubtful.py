from grounding.select_doubtful import select


def _claims():
    out = []
    for d in range(30):
        for k in range(5):
            nli = 0.9 if k % 2 == 0 else 0.1
            llm = (k % 2 == 0) if k != 4 else False  # claim 4 of each draft: checkers disagree
            out.append({"draft_id": f"d{d}", "step": k, "claim": f"c{d}-{k}", "nli_support": nli, "llm_supported": llm})
    return out


def test_every_disagreement_plus_a_random_agreement_sample():
    sel = select(_claims(), agree_per_member=5)
    for rows in sel.values():
        dis = [r for r in rows if r["stratum"] == "disagree"]
        agr = [r for r in rows if r["stratum"] == "agree"]
        assert len(dis) == 10 and len(agr) == 5  # 10 drafts per member, one disagreement each
        assert all((r["nli_support"] >= 0.5) != r["llm_supported"] for r in dis)
        assert all(r["p_include"] == 1.0 for r in dis) and all(0 < r["p_include"] < 1 for r in agr)


def test_rows_are_shuffled_so_doubtful_ones_are_not_grouped():
    rows = select(_claims(), agree_per_member=5)["R"]
    strata = [r["stratum"] for r in rows]
    assert strata != sorted(strata) and strata != sorted(strata, reverse=True)


def test_unusable_llm_verdicts_are_left_out():
    claims = _claims()
    claims[0]["llm_supported"] = None
    assert all(r["claim"] != claims[0]["claim"] for rows in select(claims, 5).values() for r in rows)
