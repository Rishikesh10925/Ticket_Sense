

PASSAGE = (
    "## Resolution steps\n1. Ask the user to try an internal resource by IP address.\n"
    "2. Run `ipconfig /all` and check that the VPN adapter lists the internal\n   DNS servers.\n"
)


def test_a_verbatim_quote_is_supported_even_when_nli_says_no():
    from grounding.claims import check_draft

    steps = [{"text": "Run `ipconfig /all` and check that the VPN adapter lists the internal DNS servers.", "citations": [1]}]
    g = check_draft(steps, {1: PASSAGE}, scorer=lambda pairs: [0.001] * len(pairs))
    assert g.claims[0].support == 1.0


def test_changed_words_never_pass_as_verbatim():
    from grounding.claims import verbatim_supported

    assert not verbatim_supported("Do not run `ipconfig /all` and check that the VPN adapter lists the internal DNS servers.", PASSAGE)
    assert not verbatim_supported("Run `ipconfig /all` and check that the VPN adapter lists the external DNS servers.", PASSAGE)
    assert not verbatim_supported("DNS servers.", PASSAGE)  # too short to count


def test_verbatim_only_counts_for_a_cited_passage():
    from grounding.claims import check_draft

    steps = [{"text": "Ask the user to try an internal resource by IP address.", "citations": [2]}]
    g = check_draft(steps, {1: PASSAGE, 2: "Unrelated text about printers."}, scorer=lambda pairs: [0.0] * len(pairs))
    assert g.claims[0].support == 0.0
