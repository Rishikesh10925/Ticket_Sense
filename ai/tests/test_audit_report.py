from grounding.audit_report import bootstrap_ci, checker_scores, report


def row(human, nli, llm, stratum="disagree", p=1.0, member="R"):
    return {"human": human, "nli_support": nli, "llm_supported": llm, "stratum": stratum,
            "p_include": p, "member": member}


def test_sampled_agreed_claims_count_by_their_weight():
    # one doubtful claim NLI gets wrong, one sampled agreed claim (standing for 10) it gets right
    rows = [row("not_supported", 0.9, False), row("supported", 0.9, True, "agree", 0.1)]
    assert checker_scores(rows, lambda r: r["nli_support"] >= 0.5)["accuracy"] == round(10 / 11, 4)


def test_error_rates_split_by_what_the_human_said():
    rows = [row("not_supported", 0.9, False), row("not_supported", 0.1, False),
            row("supported", 0.1, True), row("supported", 0.9, True)]
    s = checker_scores(rows, lambda r: r["nli_support"] >= 0.5)
    assert s["false_supported_rate"] == 0.5 and s["false_unsupported_rate"] == 0.5


def test_unclear_is_counted_but_not_scored():
    out = report([row("unclear", 0.9, True), row("supported", 0.9, True), row("", 0.9, True)])
    assert out["labelled"] == 2 and out["unclear"] == 1 and out["nli"]["accuracy"] == 1.0


def test_bootstrap_interval_contains_a_constant_metric():
    rows = [row("supported", 0.9, True, member=m) for m in "RAS"]
    assert bootstrap_ci(rows, lambda x: 1.0, n=50) == [1.0, 1.0]
