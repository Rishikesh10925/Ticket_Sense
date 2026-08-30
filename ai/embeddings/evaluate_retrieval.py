"""Evaluate department-scoped knowledge-base retrieval quality with Recall@K, against a
small hand-labelled set of test queries per department. See docs/retrieval.md.

Each test query is a realistic End User phrasing (not copied from the KB article's own
title/text) paired with the exact KB article title it should retrieve. Evaluated against
KB-article retrieval specifically (not resolved tickets too) — the hand labels are
against known KB articles, so that's the well-defined ground truth to score against.

Requires the `ai` extra and the knowledge base already embedded
(ai/embeddings/embed_knowledge_base.py).

Usage (from repo root):
    uv run --project backend --extra ai python ai/embeddings/evaluate_retrieval.py
"""

import asyncio
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2] / "backend"
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from sentence_transformers import SentenceTransformer  # noqa: E402
from sqlalchemy import select  # noqa: E402

from app.database import SessionLocal  # noqa: E402
from app.models import Department, Embedding, KnowledgeBase  # noqa: E402

from retrieve import MODEL_NAME  # noqa: E402

K = 3

# (department, query, expected KB article title)
TEST_QUERIES: list[tuple[str, str, str]] = [
    ("SAP", "I keep getting ME023 error when trying to post a goods receipt",
     "ME023: Purchase Order Item Blocked"),
    ("SAP", "My SAP account is locked and I can't log in",
     "SAP User Account Locked"),
    ("SAP", "SAP GUI keeps timing out when connecting",
     "SAP GUI Connection Timeout"),
    ("Networking", "VPN client won't connect no matter what I try",
     "VPN Client Not Connecting"),
    ("Networking", "Wifi keeps dropping throughout the day in the office",
     "Wi-Fi Repeatedly Dropping in Office"),
    ("Networking", "I need guest wifi access set up for a visitor tomorrow",
     "Requesting Guest Wi-Fi Access"),
    ("Cloud", "Getting access denied errors reading from an S3 bucket",
     "S3 Access Denied Error"),
    ("Cloud", "Our EC2 instance is unreachable over SSH",
     "EC2 Instance Unreachable via SSH"),
    ("Cloud", "TLS certificate is about to expire on our API domain",
     "TLS Certificate Expiring Warning"),
    ("Database", "Getting connection pool exhausted errors in the app",
     "Application Errors From an Exhausted Connection Pool"),
    ("Database", "A transaction failed with a deadlock error",
     "Deadlock-Triggered Transaction Rollback"),
    ("Database", "The database disk is almost full and writes are failing",
     "Database Volume Nearing or at Disk-Space Capacity"),
    ("HR", "How do I submit a request for time off",
     "How to Apply for Leave"),
    ("HR", "I can't find my payslip for this month",
     "Payroll Dates and Payslip Access"),
    ("HR", "What's the process for filing an insurance claim",
     "Health Insurance Claim Process"),
]


async def main() -> None:
    print(f"loading {MODEL_NAME} ...")
    model = SentenceTransformer(MODEL_NAME)

    async with SessionLocal() as db:
        department_cache: dict[str, Department] = {}
        per_department: dict[str, list[bool]] = {}

        for department_name, query, expected_title in TEST_QUERIES:
            if department_name not in department_cache:
                dept = await db.scalar(select(Department).where(Department.name == department_name))
                department_cache[department_name] = dept
            department = department_cache[department_name]

            query_vector = model.encode(query, normalize_embeddings=True).tolist()
            distance = Embedding.embedding.cosine_distance(query_vector)
            stmt = (
                select(KnowledgeBase.title, distance.label("distance"))
                .join(KnowledgeBase, Embedding.knowledge_base_id == KnowledgeBase.id)
                .where(KnowledgeBase.department_id == department.id)
                .order_by(distance)
                .limit(K)
            )
            rows = (await db.execute(stmt)).all()
            titles = [row.title for row in rows]
            hit = expected_title in titles

            per_department.setdefault(department_name, []).append(hit)
            marker = "HIT " if hit else "MISS"
            print(f"[{marker}] {department_name}: '{query}' -> expected '{expected_title}'")
            if not hit:
                print(f"         got: {titles}")

        print("\n=== Recall@{} per department ===".format(K))
        overall_hits = 0
        overall_total = 0
        for department_name, hits in per_department.items():
            recall = sum(hits) / len(hits)
            overall_hits += sum(hits)
            overall_total += len(hits)
            print(f"{department_name}: {sum(hits)}/{len(hits)} = {recall:.2f}")
        print(f"\nOverall: {overall_hits}/{overall_total} = {overall_hits / overall_total:.2f}")


if __name__ == "__main__":
    asyncio.run(main())
