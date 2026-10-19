"""Loads and validates data/taxonomy.yaml (Blueprint V2 §11.3, §11.4)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
TAXONOMY_PATH = REPO_ROOT / "data" / "taxonomy.yaml"
KB_DIR = REPO_ROOT / "data" / "kb"


@dataclass(frozen=True)
class Topic:
    id: str
    code: str
    name: str
    department: str
    department_code: str
    folder: str
    withheld: bool
    author: str
    existing: tuple[str, ...]

    def article_id(self, n: int) -> str:
        return f"{self.department_code}-{self.code}-{n:03d}"


@dataclass(frozen=True)
class Taxonomy:
    version: int
    articles_per_topic: int
    topics: tuple[Topic, ...]

    @property
    def departments(self) -> list[str]:
        return sorted({t.department for t in self.topics})

    def served(self) -> list[Topic]:
        return [t for t in self.topics if not t.withheld]

    def withheld(self) -> list[Topic]:
        return [t for t in self.topics if t.withheld]

    def topic(self, topic_id: str) -> Topic:
        for t in self.topics:
            if t.id == topic_id:
                return t
        raise KeyError(topic_id)


def load_taxonomy(path: Path = TAXONOMY_PATH) -> Taxonomy:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    topics = []
    for dept in raw["departments"]:
        authors = dept["authors"]
        for t in dept["topics"]:
            topics.append(
                Topic(
                    id=t["id"],
                    code=t["code"],
                    name=t["name"],
                    department=dept["name"],
                    department_code=dept["code"],
                    folder=dept["folder"],
                    withheld=bool(t["withheld"]),
                    author=t.get("author", authors[0]),
                    existing=tuple(t.get("existing", [])),
                )
            )
    return Taxonomy(raw["version"], raw["articles_per_topic"], tuple(topics))


def validate(tax: Taxonomy, kb_dir: Path = KB_DIR) -> list[str]:
    """Problems with the taxonomy; empty means valid."""
    problems: list[str] = []
    ids = [t.id for t in tax.topics]
    if len(set(ids)) != len(ids):
        problems.append("duplicate topic ids")
    for dept in tax.departments:
        dept_topics = [t for t in tax.topics if t.department == dept]
        if len(dept_topics) != 6:
            problems.append(f"{dept} has {len(dept_topics)} topics, expected 6")
        if not any(t.withheld for t in dept_topics):
            problems.append(f"{dept} has no withheld topic")
        codes = [t.code for t in dept_topics]
        if len(set(codes)) != len(codes):
            problems.append(f"{dept} has duplicate topic codes")
    if len(tax.withheld()) != 6:
        problems.append(f"{len(tax.withheld())} withheld topics, expected 6")

    seen: dict[str, str] = {}
    for t in tax.topics:
        for slug in t.existing:
            key = f"{t.folder}/{slug}"
            if key in seen:
                problems.append(f"{key} mapped to both {seen[key]} and {t.id}")
            seen[key] = t.id
            if kb_dir.exists() and not (kb_dir / t.folder / f"{slug}.md").exists():
                problems.append(f"{key}.md does not exist")
    if kb_dir.exists():
        on_disk = {f"{p.parent.name}/{p.stem}" for p in kb_dir.glob("*/*.md")}
        for unmapped in sorted(on_disk - set(seen)):
            problems.append(f"{unmapped}.md is not mapped to any topic")
    return problems


if __name__ == "__main__":
    tax = load_taxonomy()
    issues = validate(tax)
    authored = len(tax.topics) * tax.articles_per_topic
    print(f"{len(tax.topics)} topics, {len(tax.withheld())} withheld, target {authored} articles "
          f"({len(tax.served()) * tax.articles_per_topic} served)")
    for author in ("R", "A", "S"):
        n = sum(1 for t in tax.topics if t.author == author) * tax.articles_per_topic
        print(f"  author {author}: {n} articles")
    print("\n".join(issues) if issues else "taxonomy valid")
