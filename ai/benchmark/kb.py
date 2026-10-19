"""Loads and validates knowledge-base articles in the V2 template
(docs/kb-article-template.md). Used by ingestion, the ticket generator and the judge.

V1 articles (no front matter) still load, so ingestion keeps working while the 60 V1
articles are converted during Weeks 2 and 3. `is_v2` tells them apart.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # ai/, when run as a script

from benchmark.taxonomy import KB_DIR, Taxonomy, load_taxonomy

SECTIONS = ("Symptom", "Cause", "Resolution steps", "Warnings", "Key facts")
_FRONT_MATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)
_SECTION_RE = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
_ID_RE = re.compile(r"^[A-Z]+-[A-Z]+-\d{3}$")
_STEP_RE = re.compile(r"^\s*\d+\.\s+", re.MULTILINE)
_BULLET_RE = re.compile(r"^\s*-\s+(.+?)\s*$", re.MULTILINE)


@dataclass
class Article:
    path: Path
    title: str
    body: str  # markdown without front matter
    meta: dict = field(default_factory=dict)
    sections: dict[str, str] = field(default_factory=dict)

    @property
    def is_v2(self) -> bool:
        return bool(self.meta)

    @property
    def id(self) -> str | None:
        return self.meta.get("id")

    @property
    def topic(self) -> str | None:
        return self.meta.get("topic")

    @property
    def served(self) -> bool:
        return bool(self.meta.get("served", True))

    @property
    def updated(self) -> date | None:
        value = self.meta.get("updated")
        return value if isinstance(value, date) else (date.fromisoformat(value) if value else None)

    @property
    def key_facts(self) -> list[str]:
        return _BULLET_RE.findall(self.sections.get("Key facts", ""))

    @property
    def steps(self) -> list[str]:
        text = self.sections.get("Resolution steps", "")
        parts = _STEP_RE.split(text)
        return [" ".join(p.split()) for p in parts if p.strip()]

    def retrieval_text(self) -> str:
        """What gets embedded and searched: everything a reader of the article sees,
        except the key facts, which exist for the judge and would make retrieval
        artificially easy if indexed."""
        keep = [f"## {name}\n{self.sections[name]}" for name in SECTIONS[:-1] if name in self.sections]
        if not keep:  # V1 article
            return self.body
        return f"# {self.title}\n\n" + "\n\n".join(keep)


def parse_article(path: Path) -> Article:
    text = path.read_text(encoding="utf-8")
    meta: dict = {}
    match = _FRONT_MATTER_RE.match(text)
    if match:
        meta = yaml.safe_load(match.group(1)) or {}
        body = text[match.end():]
    else:
        body = text

    sections: dict[str, str] = {}
    heads = list(_SECTION_RE.finditer(body))
    for i, head in enumerate(heads):
        end = heads[i + 1].start() if i + 1 < len(heads) else len(body)
        sections[head.group(1).strip()] = body[head.end():end].strip()

    if meta.get("title"):
        title = str(meta["title"])
    else:
        first = next((line for line in body.splitlines() if line.strip()), "")
        title = first.lstrip("# ").strip()
    return Article(path=path, title=title, body=body, meta=meta, sections=sections)


def load_articles(kb_dir: Path = KB_DIR) -> list[Article]:
    return [parse_article(p) for p in sorted(kb_dir.glob("*/*.md"))]


def validate_article(article: Article, taxonomy: Taxonomy) -> list[str]:
    """Template problems for one V2 article; empty means valid."""
    if not article.is_v2:
        return [f"{article.path.name}: V1 article, not yet converted"]
    name = article.path.name
    problems: list[str] = []
    for key in ("id", "department", "topic", "title", "updated", "served", "author"):
        if key not in article.meta:
            problems.append(f"{name}: front matter missing '{key}'")
    if article.id and not _ID_RE.match(article.id):
        problems.append(f"{name}: id '{article.id}' is not DEPT-TOPIC-NNN")
    if article.id and article.path.stem != article.id:
        problems.append(f"{name}: file name does not match id {article.id}")
    try:
        topic = taxonomy.topic(article.topic or "")
    except KeyError:
        problems.append(f"{name}: unknown topic '{article.topic}'")
        topic = None
    if topic is not None:
        if article.meta.get("department") != topic.department:
            problems.append(f"{name}: department does not match topic {topic.id}")
        if article.served == topic.withheld:
            problems.append(f"{name}: served={article.served} but topic withheld={topic.withheld}")
        if article.id and not article.id.startswith(f"{topic.department_code}-{topic.code}-"):
            problems.append(f"{name}: id prefix does not match topic code {topic.department_code}-{topic.code}")
        if article.path.parent.name != topic.folder:
            problems.append(f"{name}: stored under {article.path.parent.name}/, expected {topic.folder}/")
    missing = [s for s in SECTIONS if s not in article.sections]
    if missing:
        problems.append(f"{name}: missing sections {missing}")
    if list(article.sections) != [s for s in SECTIONS if s in article.sections]:
        problems.append(f"{name}: sections out of order")
    if not 3 <= len(article.key_facts) <= 6:
        problems.append(f"{name}: {len(article.key_facts)} key facts, expected 3 to 6")
    if len(article.steps) < 2:
        problems.append(f"{name}: fewer than two numbered resolution steps")
    return problems


def review_status(articles: list[Article]) -> tuple[int, int]:
    """(V2 articles, of which human-reviewed). An article counts as reviewed only when a
    second team member is named in `reviewer` (docs/kb-article-template.md checklist)."""
    v2 = [a for a in articles if a.is_v2]
    return len(v2), sum(1 for a in v2 if a.meta.get("reviewer"))


if __name__ == "__main__":
    tax = load_taxonomy()
    articles = load_articles()
    v2_problems = [p for a in articles if a.is_v2 for p in validate_article(a, tax)]
    n_v2, n_reviewed = review_status(articles)
    print(f"{len(articles)} articles on disk: {n_v2} in V2 template ({n_reviewed} human-reviewed), "
          f"{len(articles) - n_v2} V1 awaiting conversion")
    print("\n".join(v2_problems) if v2_problems else "all V2 articles valid")
