"""Generate embeddings for the authored knowledge-base articles.

Reads every db/seed/knowledge_base/<department>/*.md article, upserts it into the
`knowledge_base` table, embeds its content with sentence-transformers/all-MiniLM-L6-v2
(384-dim, matching backend/app/models/embedding.py's EMBEDDING_DIM and
docs/architecture.md), and stores the result in the `embeddings` table. Safe to re-run —
articles and their embeddings are replaced by title, not duplicated.

Requires the `ai` extra: `uv sync --extra ai` (pulls in sentence-transformers/torch,
kept out of the default backend install — see backend/pyproject.toml).

Usage (from repo root):
    uv run --project backend --extra ai python ai/embeddings/embed_knowledge_base.py
"""

import asyncio
import sys
from pathlib import Path

from sentence_transformers import SentenceTransformer
from sqlalchemy import delete, select

# ai/embeddings/embed_knowledge_base.py -> repo_root/backend must be importable.
BACKEND_DIR = Path(__file__).resolve().parents[2] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.database import SessionLocal  # noqa: E402
from app.models import Department, Embedding, KnowledgeBase  # noqa: E402

KB_DIR = Path(__file__).resolve().parents[2] / "db" / "seed" / "knowledge_base"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

FOLDER_TO_DEPARTMENT = {
    "sap": "SAP",
    "networking": "Networking",
    "cloud": "Cloud",
    "database": "Database",
    "hr": "HR",
}


def _parse_article(path: Path) -> tuple[str, str]:
    text = path.read_text(encoding="utf-8")
    title = text.splitlines()[0].lstrip("# ").strip()
    return title, text


async def main() -> None:
    print(f"loading {MODEL_NAME} ...")
    model = SentenceTransformer(MODEL_NAME)

    async with SessionLocal() as db:
        department_cache: dict[str, Department] = {}
        embedded = 0

        for folder in sorted(KB_DIR.iterdir()):
            if not folder.is_dir():
                continue
            department_name = FOLDER_TO_DEPARTMENT.get(folder.name)
            if department_name is None:
                print(f"skip unknown department folder: {folder.name}")
                continue

            if department_name not in department_cache:
                dept = await db.scalar(select(Department).where(Department.name == department_name))
                if dept is None:
                    dept = Department(name=department_name)
                    db.add(dept)
                    await db.flush()
                department_cache[department_name] = dept
            department = department_cache[department_name]

            for article_path in sorted(folder.glob("*.md")):
                title, content = _parse_article(article_path)

                article = await db.scalar(
                    select(KnowledgeBase).where(
                        KnowledgeBase.department_id == department.id,
                        KnowledgeBase.title == title,
                    )
                )
                if article is None:
                    article = KnowledgeBase(department_id=department.id, title=title, content=content)
                    db.add(article)
                    await db.flush()
                else:
                    article.content = content
                    await db.flush()

                await db.execute(delete(Embedding).where(Embedding.knowledge_base_id == article.id))
                vector = model.encode(content, normalize_embeddings=True).tolist()
                db.add(
                    Embedding(
                        knowledge_base_id=article.id,
                        chunk_index=0,
                        chunk_text=content,
                        embedding=vector,
                    )
                )
                embedded += 1
                print(f"embedded: {department_name}/{title}")

        await db.commit()

    print(f"\n{embedded} articles embedded.")


if __name__ == "__main__":
    asyncio.run(main())
