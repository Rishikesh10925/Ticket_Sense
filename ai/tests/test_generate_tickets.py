import json
import random

from benchmark.generate_tickets import (
    copies_article,
    generate,
    inject_typos,
    plan_scenarios,
    sample_body_length,
    type_quotas,
)
from generation.llm import FakeLLMClient


def test_type_quotas_sum_exactly():
    for n in (10, 99, 100, 101, 1800):
        quotas = type_quotas(n)
        assert sum(quotas.values()) == n
    assert type_quotas(100) == {"A": 55, "B": 15, "C1": 20, "C2": 10}


def test_typos_are_deterministic_and_spare_codes():
    text = "The background job SM37 status stays released for hours error 809 again"
    a = inject_typos(text, random.Random(1), rate=1.0)
    assert a == inject_typos(text, random.Random(1), rate=1.0)
    assert a != text
    assert "SM37" in a and "809" in a


def test_body_length_follows_style_profile():
    rng = random.Random(0)
    lengths = [sample_body_length(rng) for _ in range(500)]
    assert 12 <= min(lengths) and max(lengths) <= 90
    assert 40 <= sorted(lengths)[250] <= 70


def _sap_article():
    return next(s.article for s in plan_scenarios(30, departments={"SAP"}) if s.article is not None)


def test_copy_check_flags_solution_text_but_allows_symptom():
    article = _sap_article()
    step = article.steps[0]
    assert copies_article(f"Hi, {step} but it still fails.", article)
    assert not copies_article(article.sections["Symptom"], article)


def test_generate_builds_typed_records_and_appends_b_question():
    def responder(req):
        return json.dumps({
            "subject": "Problem with SAP today",
            "body": "Something in SAP is not working as I expected this morning, can you help me please.",
            "attachment_text": "",
            "uncovered_question": "How long does this usually take?",
        })

    records = generate(plan_scenarios(30, departments={"SAP"}), FakeLLMClient(responder), 30)
    assert len(records) == 30
    assert {r.type for r in records} == {"A", "B", "C1", "C2"}
    for r in records:
        if r.type == "B":
            assert r.body.endswith("How long does this usually take?")
        else:
            assert r.uncovered_question is None
        assert (r.gold_articles == []) == (r.type == "C2")
        assert r.prompt_version == "ticket-v1"


def test_generate_rejects_tickets_that_copy_the_solution():
    scenario = next(s for s in plan_scenarios(30, departments={"SAP"}) if s.type == "A")
    leak = scenario.article.steps[0]
    calls = {"n": 0}

    def responder(req):
        calls["n"] += 1
        return json.dumps({"subject": "Help", "body": leak, "uncovered_question": "Why?"})

    stats: dict = {}
    records = generate([scenario], FakeLLMClient(responder), 3, stats=stats)
    assert records == [] and stats["failed"] >= 1 and stats["rejected"] >= 3
