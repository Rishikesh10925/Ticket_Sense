from security.pii import redact, restore


def test_email_phone_and_secret_are_redacted():
    text = (
        "Hi, I'm locked out. Reach me at priya.s@example.com or +91 98765 43210. "
        "My old password: Summer@2026 stopped working."
    )
    r = redact(text)
    assert "priya.s@example.com" not in r.text
    assert "98765 43210" not in r.text
    assert "Summer@2026" not in r.text
    assert "[EMAIL_1]" in r.text and "[PHONE_1]" in r.text and "password: [SECRET_1]" in r.text
    assert restore(r.text, r.mapping) == text


def test_indian_ids_and_luhn_valid_cards_are_redacted():
    r = redact("PAN ABCDE1234F, Aadhaar 2345 6789 0123, card 4111 1111 1111 1111.")
    assert r.counts == {"PAN": 1, "AADHAAR": 1, "CARD": 1}


def test_a_long_number_that_fails_luhn_is_not_a_card():
    # 16 digits, but not a valid card number: left for the other rules (here: none).
    assert "CARD" not in redact("ref 1234 5678 9012 3456").text


def test_diagnostic_values_are_kept():
    text = "VPN error 619 on 10.20.30.40:443, IDoc status 51, ticket INC0012345, port 3200, employee E10234."
    assert redact(text).text == text


def test_same_value_gets_the_same_placeholder_across_fields():
    mapping: dict[str, str] = {}
    subject = redact("Contact a.b@example.com", mapping)
    body = redact("Again: a.b@example.com and c.d@example.com", mapping)
    assert subject.text == "Contact [EMAIL_1]"
    assert body.text == "Again: [EMAIL_1] and [EMAIL_2]"


def test_empty_text():
    assert redact(None).text == "" and redact("").mapping == {}


def test_log_timestamps_are_not_phone_numbers():
    text = "2026-10-19 12:30:01 ERROR job ZFI_POST cancelled"
    assert redact(text).text == text
