"""Fact-check checklist for a department's KB articles (docs/kb-authoring-workflow.md).

Lists, per article, the technical terms a human reviewer must verify against vendor
documentation (transaction codes, profile parameters, status numbers, commands), each
with a ready-made search link, plus the article's key facts. It only points at what to
check: whether each fact is right is the reviewer's call, recorded by setting
`reviewer:` in the article.

    python ai/benchmark/kb_checklist.py --department sap --reviewer R
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import quote_plus

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ai"))

from benchmark.kb import load_articles  # noqa: E402

VENDOR = {
    "sap": ("SAP", "help.sap.com"),
    "cloud": ("AWS", "docs.aws.amazon.com"),
    "database": ("PostgreSQL", "postgresql.org/docs"),
    "networking": ("Windows", "learn.microsoft.com"),
    "hr": ("", ""),
}
_CODE = re.compile(r"`([^`]{2,60})`")
_TCODE = re.compile(r"\b([A-Z]{2,5}\d{1,3}[A-Z]?|[A-Z]{4,6}\d?)\b")
_STATUS = re.compile(r"\b(?:status|error|code)\s+(\d{2,4})\b", re.IGNORECASE)
_NOT_TERMS = {"SAP", "GUI", "PO", "GR", "IR", "MM", "FI", "HR", "IT", "ID", "IDoc", "RFC", "SSH", "VPN", "DNS",
              "URL", "MFA", "SSO", "PDF", "CSV", "API", "USB", "LAN", "WAN", "HTTP", "HTTPS", "TCP", "UDP", "AND",
              "THE", "NOT", "BASIS", "FIORI", "ABAP", "SM"}


def terms(text: str) -> list[str]:
    found = [m.strip() for m in _CODE.findall(text)]
    found += [t for t in _TCODE.findall(text) if t not in _NOT_TERMS and set(t) != {"X"}]
    found += [f"status {s}" for s in _STATUS.findall(text)]
    return list(dict.fromkeys(found))


def search(term: str, vendor: str, site: str) -> str:
    q = f"{vendor} {term}".strip()
    return f"[{term}](https://www.google.com/search?q={quote_plus(q + (' site:' + site if site else ''))})"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--department", default="sap")
    parser.add_argument("--reviewer", default="R", help="your initial: articles you wrote are skipped")
    args = parser.parse_args()
    vendor, site = VENDOR[args.department]
    # Articles whose risky claims the authoring workflow lists first (docs/kb-authoring-workflow.md).
    workflow = (ROOT / "docs" / "kb-authoring-workflow.md").read_text(encoding="utf-8")
    priority = set(re.findall(r"^\| ([A-Z]+-[A-Z]+-\d{3}) \|", workflow, flags=re.MULTILINE))
    articles = [a for a in load_articles(ROOT / "data" / "kb") if a.path.parent.name == args.department
                and a.meta.get("author") != args.reviewer]
    lines = [
        f"# Fact-check checklist: {args.department.upper()} ({len(articles)} articles, reviewer {args.reviewer})",
        "",
        "For each article: open it, click each term, confirm the article uses it correctly.",
        f"All correct ➜ set `reviewer: {args.reviewer}` in the article. Something wrong ➜ note it here and tell Claude.",
        "Values described as *this organisation's* policy (limits, approvals) are fictional company rules:",
        "they cannot be looked up, only checked for being stated as policy rather than as a vendor default.",
        "⭐ = check first (claims the authoring workflow flagged as risky). ⬜ = not checked yet. ✅ = reviewed.",
        "",
    ]
    for a in sorted(articles, key=lambda a: (a.id not in priority, a.id)):
        done = "✅" if a.meta.get("reviewer") else ("⭐" if a.id in priority else "⬜")
        body = a.path.read_text(encoding="utf-8")
        lines += [f"## {done} {a.id}: {a.meta.get('title')}",
                  f"File: [{a.path.relative_to(ROOT).as_posix()}](../../{a.path.relative_to(ROOT).as_posix()}) · "
                  f"author {a.meta.get('author')}", ""]
        t = terms(body)
        lines.append("**Look up:** " + (" · ".join(search(x, vendor, site) for x in t) if t else "(no technical terms; check the steps make sense)"))
        lines += ["", "**Key facts to confirm:**"] + [f"- [ ] {k}" for k in a.key_facts] + ["", "Notes: ", ""]
    out = ROOT / "docs" / "kb-review" / f"{args.department}-checklist.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{len(articles)} articles -> {out}")


if __name__ == "__main__":
    main()
