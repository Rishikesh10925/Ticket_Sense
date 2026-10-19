from grounding.claims import check_draft, split_claims


def test_split_claims_into_sentences_and_clauses():
    text = "Open SU01 for the user; unlock the account. Then set an initial password, then tell the user."
    assert split_claims(text) == [
        "Open SU01 for the user",
        "unlock the account.",
        "Then set an initial password",
        "tell the user.",
    ]


def test_short_fragments_merge_into_previous_claim():
    assert split_claims("Restart the VPN client. Retry.") == ["Restart the VPN client. Retry."]


def _keyword_scorer(pairs):
    # Fake NLI: "entailed" when every word of the claim appears in the premise.
    return [1.0 if set(h.lower().strip(".").split()) <= set(p.lower().replace(".", "").split()) else 0.1
            for p, h in pairs]


def test_check_draft_scores_against_cited_passages_only():
    passages = {1: "Retry from a mobile hotspot.", 2: "Disable the firewall."}
    steps = [
        {"text": "Retry from a mobile hotspot.", "citations": [1]},
        {"text": "Disable the firewall.", "citations": [1]},  # true in passage 2, but it cites 1
        {"text": "Reinstall Windows.", "citations": [9]},  # cites a passage that does not exist
    ]
    g = check_draft(steps, passages, scorer=_keyword_scorer)
    supports = [c.support for c in g.claims]
    assert supports == [1.0, 0.1, 0.0]
    assert g.groundedness == round(1 / 3, 4) and g.min_support == 0.0
    assert [c.text for c in g.weakest(2)] == ["Reinstall Windows.", "Disable the firewall."]


def test_long_passages_are_also_checked_in_windows():
    filler = " ".join(f"Sentence {i} is about something else entirely." for i in range(20))
    passages = {1: filler + " Retry from a mobile hotspot."}
    seen = []

    def scorer(pairs):
        seen.extend(pairs)
        return [1.0 if p.strip().endswith("hotspot.") and len(p.split()) < 40 else 0.0 for p, _ in pairs]

    g = check_draft([{"text": "Retry from a mobile hotspot.", "citations": [1]}], passages, scorer=scorer)
    assert g.groundedness == 1.0 and len(seen) > 1


def test_empty_draft_has_no_groundedness():
    g = check_draft([], {1: "x"}, scorer=_keyword_scorer)
    assert g.groundedness is None and g.claims == ()
