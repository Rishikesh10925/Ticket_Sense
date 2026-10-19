"""PII redaction before model calls and logs (Blueprint V2 §9 stage 1, §16).

Ticket text is redacted at intake. Everything downstream (classifier, retrieval and its
run log, the drafter, the claim checker, the LLM cache) only ever sees placeholders
such as `[EMAIL_1]`. The redaction map (placeholder -> original) is stored on the
ticket row, which already holds the original text, so an engineer can restore the
values in a reply; it is never sent to a model or written to a log.

Covered: e-mail addresses, phone numbers (Indian and international formats), Aadhaar
and PAN numbers, payment-card numbers (Luhn-checked), and secrets written as
"password: ..." or "pin: ...". Not covered: personal names in free text, which need a
named-entity model; the repository only holds synthetic data, so this is a stated
limitation (Blueprint V2 §16), not a silent one.

IP addresses, hostnames, error codes and employee IDs are deliberately kept: they are
diagnostic for IT tickets, and redacting them would break retrieval and drafting.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

REDACTOR_VERSION = "pii-v1"

_EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
# Secrets first: "password: hunter2" must not survive as a phone or card match.
_SECRET = re.compile(r"(?i)\b(password|passwd|pwd|passcode|pin|otp)\b(\s*(?:is|=|:)\s*)(\S+)")
_PAN = re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b")
_AADHAAR = re.compile(r"\b[2-9][0-9]{3}[ -]?[0-9]{4}[ -]?[0-9]{4}\b")
_CARD = re.compile(r"\b(?:\d[ -]?){12,18}\d\b")
_DATE = re.compile(r"\b(19|20)\d{2}-\d{2}-\d{2}\b")
_PHONE = re.compile(r"(?<![\w.])\+?\(?\d[\d ()-]{8,18}\d(?![\d.]\d)(?!\w)")


@dataclass
class Redaction:
    text: str
    mapping: dict[str, str] = field(default_factory=dict)  # placeholder -> original

    @property
    def counts(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for placeholder in self.mapping:
            kind = placeholder.strip("[]").rsplit("_", 1)[0]
            out[kind] = out.get(kind, 0) + 1
        return out


def _luhn_ok(digits: str) -> bool:
    total, parity = 0, len(digits) % 2
    for i, ch in enumerate(digits):
        d = int(ch)
        if i % 2 == parity:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


class _Redactor:
    def __init__(self, mapping: dict[str, str]):
        self.mapping = mapping
        self.reverse = {v: k for k, v in mapping.items()}

    def placeholder(self, kind: str, original: str) -> str:
        if original in self.reverse:
            return self.reverse[original]
        n = sum(1 for p in self.mapping if p.startswith(f"[{kind}_")) + 1
        token = f"[{kind}_{n}]"
        self.mapping[token] = original
        self.reverse[original] = token
        return token

    def run(self, text: str) -> str:
        text = _SECRET.sub(lambda m: m.group(1) + m.group(2) + self.placeholder("SECRET", m.group(3)), text)
        text = _EMAIL.sub(lambda m: self.placeholder("EMAIL", m.group(0)), text)
        text = _PAN.sub(lambda m: self.placeholder("PAN", m.group(0)), text)

        def card(m: re.Match) -> str:
            digits = re.sub(r"\D", "", m.group(0))
            return self.placeholder("CARD", m.group(0)) if 13 <= len(digits) <= 19 and _luhn_ok(digits) else m.group(0)

        text = _CARD.sub(card, text)
        text = _AADHAAR.sub(lambda m: self.placeholder("AADHAAR", m.group(0)), text)

        def phone(m: re.Match) -> str:
            digits = re.sub(r"\D", "", m.group(0))
            if _DATE.search(m.group(0)):
                return m.group(0)  # a timestamp in a pasted log, not a phone number
            # 10+ digits: a phone number. Shorter runs are error codes, ports or IDs.
            return self.placeholder("PHONE", m.group(0)) if 10 <= len(digits) <= 13 else m.group(0)

        return _PHONE.sub(phone, text)


def redact(text: str | None, mapping: dict[str, str] | None = None) -> Redaction:
    """Redact one text. Pass the same `mapping` across a ticket's fields so a value
    that appears in the subject and the body gets the same placeholder."""
    mapping = {} if mapping is None else mapping
    if not text:
        return Redaction(text or "", mapping)
    return Redaction(_Redactor(mapping).run(text), mapping)


def restore(text: str, mapping: dict[str, str]) -> str:
    """Put the original values back, e.g. into a reply the engineer is about to send."""
    for placeholder, original in mapping.items():
        text = text.replace(placeholder, original)
    return text
