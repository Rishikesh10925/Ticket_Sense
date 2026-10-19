"""Generate embeddings for the authored knowledge-base articles.

Reads every data/kb/<department>/*.md article, upserts it into the
`knowledge_base` table, embeds its content with sentence-transformers/all-MiniLM-L6-v2
(384-dim, matching backend/app/models/embedding.py's EMBEDDING_DIM and
docs/architecture.md), and stores the result in the `embeddings` table. Safe to re-run —
articles and their embeddings are replaced by title, not duplicated.

Requires the `ai` extra: `uv sync --extra ai` (pulls in sentence-transformers/torch,
kept out of the default backend install — see backend/pyproject.toml).

V2 template articles (front matter, docs/kb-article-template.md) are matched by their
article id and stored with topic, served flag and `updated` date; their key facts are
not embedded (ai/benchmark/kb.py, Article.retrieval_text). V1 articles still load.
Each file-sourced row records its path in `source_url` ("kb:data/kb/...").

Usage (from repo root):
    uv run --project backend --extra ai python ai/embeddings/embed_knowledge_base.py [--prune-stale]

--prune-stale deletes KB rows that no file produces any more (for example a V1 article
converted to a V2 id). Without it they are only listed, since admin-created articles
look the same.
"""

import asyncio
import sys
from datetime import datetime, time, timezone
from pathlib import Path

from sentence_transformers import SentenceTransformer
from sqlalchemy import delete, select

# ai/embeddings/embed_knowledge_base.py -> repo_root/backend must be importable.
BACKEND_DIR = Path(__file__).resolve().parents[2] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.database import SessionLocal  # noqa: E402
from app.models import Department, Embedding, KBChunk, KnowledgeBase  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # ai/
from benchmark.kb import parse_article  # noqa: E402
from benchmark.taxonomy import load_taxonomy  # noqa: E402
from chunking import chunk_article  # noqa: E402

KB_DIR = Path(__file__).resolve().parents[2] / "data" / "kb"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

FOLDER_TO_DEPARTMENT = {
    "sap": "SAP",
    "networking": "Networking",
    "cloud": "Cloud",
    "database": "Database",
    "hr": "HR",
}


REPO_ROOT = Path(__file__).resolve().parents[2]


async def main(prune_stale: bool = False) -> None:
    print(f"loading {MODEL_NAME} ...")
    model = SentenceTransformer(MODEL_NAME)

    topic_names = {t.id: t.name for t in load_taxonomy().topics}

    async with SessionLocal() as db:
        department_cache: dict[str, Department] = {}
        embedded = 0
        n_chunks = 0
        produced: set[str] = set()
        kept_ids: set = set()

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
                parsed = parse_article(article_path)
                title, content = parsed.title, parsed.retrieval_text()
                source = "kb:" + article_path.relative_to(REPO_ROOT).as_posix()
                produced.add(source)

                if parsed.id:
                    lookup = KnowledgeBase.article_key == parsed.id
                else:
                    lookup = (KnowledgeBase.department_id == department.id) & (KnowledgeBase.title == title)
                article = await db.scalar(select(KnowledgeBase).where(lookup))
                if article is None:
                    article = KnowledgeBase(department_id=department.id, title=title, content=content)
                    db.add(article)
                article.title = title
                article.content = content
                article.source_url = source
                article.article_key = parsed.id
                article.topic = parsed.topic
                article.served = parsed.served
                if parsed.updated is not None:
                    article.updated_at = datetime.combine(parsed.updated, time(), tzinfo=timezone.utc)
                await db.flush()
                kept_ids.add(article.id)

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

                # Section chunks with dense + full-text vectors (kb_chunks, migration 0012).
                await db.execute(delete(KBChunk).where(KBChunk.knowledge_base_id == article.id))
                chunks = chunk_article(parsed.title, topic_names.get(parsed.topic or ""), parsed.sections)
                chunk_vectors = model.encode([c.text for c in chunks], normalize_embeddings=True) if chunks else []
                for chunk, chunk_vector in zip(chunks, chunk_vectors):
                    db.add(
                        KBChunk(
                            knowledge_base_id=article.id,
                            chunk_index=chunk.index,
                            sections=",".join(chunk.sections),
                            text=chunk.text,
                            n_tokens=chunk.n_tokens,
                            embedding=chunk_vector.tolist(),
                        )
                    )
                n_chunks += len(chunks)
                embedded += 1
                print(f"embedded: {department_name}/{parsed.id or title}{'' if parsed.served else ' (withheld)'}")

        seeded_departments = [d.id for d in department_cache.values()]
        stale = [
            row
            for row in await db.scalars(select(KnowledgeBase).where(KnowledgeBase.department_id.in_(seeded_departments)))
            if row.id not in kept_ids and (row.source_url is None or row.source_url.startswith("kb:"))
        ]
        for row in stale:
            if prune_stale:
                await db.execute(delete(Embedding).where(Embedding.knowledge_base_id == row.id))
                await db.delete(row)
            print(f"{'pruned' if prune_stale else 'stale (use --prune-stale)'}: {row.title}")

        await db.commit()

    print(f"\n{embedded} articles embedded, {n_chunks} chunks written to kb_chunks.")


if __name__ == "__main__":
    asyncio.run(main(prune_stale="--prune-stale" in sys.argv))
