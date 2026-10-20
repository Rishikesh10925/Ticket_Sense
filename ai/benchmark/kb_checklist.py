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
import html
import re
import sys
from pathlib import Path
from urllib.parse import quote_plus

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ai"))

from benchmark.kb import is_ai_reviewed, is_human_reviewed, load_articles  # noqa: E402

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
        "⭐ = check first (flagged as risky). ⬜ = not checked. 🤖 = AI-checked only (still needs a human). ✅ = human-reviewed.",
        "",
    ]
    for a in sorted(articles, key=lambda a: (a.id not in priority, a.id)):
        done = "✅" if is_human_reviewed(a) else "🤖" if is_ai_reviewed(a) else ("⭐" if a.id in priority else "⬜")
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
    page = out.with_suffix(".html")
    page.write_text(to_html(lines, args.department), encoding="utf-8")
    print(f"{len(articles)} articles -> {out} and {page.name}")


_LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


def _inline(text: str) -> str:
    text = html.escape(text, quote=False)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    return _LINK.sub(lambda m: f'<a href="{m.group(2)}" target="_blank" rel="noopener">{m.group(1)}</a>', text)


def to_html(lines: list[str], department: str) -> str:
    """The same checklist as a browser page: clickable links, tickable facts."""
    body = []
    for line in lines:
        if line.startswith("# "):
            body.append(f"<h1>{_inline(line[2:])}</h1>")
        elif line.startswith("## "):
            body.append(f'</section><section class="card"><h2>{_inline(line[3:])}</h2>')
        elif line.startswith("- [ ] "):
            body.append(f"<label class=fact><input type=checkbox> {_inline(line[6:])}</label>")
        elif line.startswith("Notes:"):
            body.append('<textarea placeholder="Notes: anything wrong or doubtful? Tell Claude."></textarea>')
        elif line.strip():
            body.append(f"<p>{_inline(line)}</p>")
    style = (
        ":root{--bg:#f8fafc;--card:#fff;--text:#0f172a;--muted:#64748b;--border:#e2e8f0;--link:#4f46e5}"
        "@media (prefers-color-scheme:dark){:root{--bg:#0b1120;--card:#131c31;--text:#e2e8f0;--muted:#94a3b8;"
        "--border:#1e293b;--link:#a5b4fc}}"
        "body{margin:0;background:var(--bg);color:var(--text);font:15px/1.6 system-ui,sans-serif}"
        "main{max-width:900px;margin:0 auto;padding:16px}h1{font-size:22px}"
        ".card{background:var(--card);border:1px solid var(--border);border-radius:8px;padding:4px 16px 12px;margin:14px 0}"
        "h2{font-size:17px}a{color:var(--link)}code{font-size:13px}p{margin:6px 0}"
        ".fact{display:block;margin:4px 0;cursor:pointer}"
        "textarea{width:100%;min-height:44px;margin-top:6px;font:inherit;background:var(--bg);color:var(--text);"
        "border:1px solid var(--border);border-radius:6px;padding:6px;box-sizing:border-box}"
    )
    return (
        "<!doctype html><html lang=en><head><meta charset=utf-8>"
        "<meta name=viewport content='width=device-width, initial-scale=1'>"
        f"<title>{department.upper()} fact-check</title><style>{style}</style></head>"
        "<body><main><section>" + "\n".join(body) + "</section></main></body></html>\n"
    )


if __name__ == "__main__":
    main()
