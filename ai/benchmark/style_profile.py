"""Style statistics from the public ticket dataset (ADR 003: style reference only).

Writes data/benchmark/style_profile.json: aggregate numbers that set the ticket
generator's noise levels (length, greetings, lower-case starts, missing punctuation,
error codes). No ticket text is copied; the dataset is CC-BY-NC and is never shipped.

Usage: uv run --project backend python ai/benchmark/style_profile.py
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw" / "customer-support-tickets" / "aa_dataset-tickets-multi-lang-5-2-50-version.csv"
OUT = ROOT / "data" / "benchmark" / "style_profile.json"

GREETING = re.compile(r"^\s*(?:dear|hello|hi|hey|good (?:morning|afternoon|evening)|greetings)\b", re.I)
SIGN_OFF = re.compile(r"(?:regards|thank you|thanks|sincerely|best)[,!.\s]*(?:\n.*)?$", re.I | re.S)
ERROR_CODE = re.compile(r"\b(?:[A-Z]{1,4}[-_ ]?\d{2,5}|0x[0-9A-Fa-f]{4,8}|error \d{2,5})\b")
PLACEHOLDER = re.compile(r"<[^>]+>")


def profile(texts: pd.Series) -> dict:
    texts = texts.dropna().astype(str)
    words = texts.str.split().str.len()
    first_alpha = texts.str.extract(r"([A-Za-z])", expand=False).fillna("A")
    return {
        "n": int(texts.size),
        "words_quantiles": {str(q): float(np.quantile(words, q)) for q in (0.1, 0.25, 0.5, 0.75, 0.9)},
        "share_greeting": round(float(texts.str.match(GREETING).mean()), 3),
        "share_sign_off": round(float(texts.str.contains(SIGN_OFF).mean()), 3),
        "share_lowercase_start": round(float(first_alpha.str.islower().mean()), 3),
        "share_no_final_punctuation": round(float((~texts.str.strip().str[-1:].isin(list(".!?"))).mean()), 3),
        "share_question_mark": round(float(texts.str.contains(r"\?").mean()), 3),
        "share_error_code": round(float(texts.str.contains(ERROR_CODE).mean()), 3),
        "share_placeholder_tokens": round(float(texts.str.contains(PLACEHOLDER).mean()), 3),
        "share_multi_paragraph": round(float(texts.str.contains(r"\n\s*\n").mean()), 3),
    }


def main() -> None:
    df = pd.read_csv(RAW)
    en = df[df["language"] == "en"]
    result = {
        "source": "Tobi-Bueck/customer-support-tickets (CC-BY-NC-4.0), English rows; aggregate statistics only",
        "subject": profile(en["subject"]),
        "body": profile(en["body"]),
        "share_missing_subject": round(float(en["subject"].isna().mean()), 3),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
