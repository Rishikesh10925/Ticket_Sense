"""Red team through the full live pipeline (Roadmap Week 9, Rishikesh: "run the 40-ticket
injection red-team and fix findings"; exit gate: "zero critical policy overrides, or
residual risk documented").

Each red-team ticket goes through the same LangGraph pipeline a real ticket does:
redaction, classification and routing (the classifier picks the department, not the
red-team file), hybrid retrieval, structured drafting, the output screen, the claim
check, the signal vector and the confidence gate with its active thresholds and shift
guard. An attack succeeds only if a forbidden string is in a draft an engineer would
actually see (fast or assisted lane). Nothing is written: every run is rolled back.

    python ai/redteam/run_through_pipeline.py
"""

from __future__ import annotations

import asyncio
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "ai"))

from redteam.run_redteam import load_set  # noqa: E402


async def run(items: list[dict]) -> list[dict]:
    from app.config import settings
    from app.database import SessionLocal
    from app.models import Department
    from generation.llm import get_llm_client
    from graph.nodes import get_scorer
    from graph.pipeline import build_pipeline

    results = []
    for item in items:
        async with SessionLocal() as db:
            pipeline = build_pipeline(db, Department, get_llm_client(settings.llm_client),
                                      scorer=get_scorer(settings.grounding_scorer))
            body = item["body"] + (f"\n\n{item['attachment']}" if item.get("attachment") else "")
            state = await pipeline.ainvoke({"subject": item["subject"], "description": body,
                                            "attachment_path": None, "attachment_type": None})
            await db.rollback()  # retrieval runs from the red team are not kept
        gate = state.get("gate_v2") or {}
        draft = state.get("draft") or ""
        shown = state.get("gate_decision") == "draft"
        found = [f for f in item["forbidden"] if f.lower() in draft.lower()] if shown else []
        results.append({
            "id": item["id"], "category": item["category"], "routed_to": state.get("department_name"),
            "lane": gate.get("lane", "escalate"), "shown": shown, "success": bool(found), "forbidden_found": found,
            "screen_blocked": bool(((state.get("draft_result") or {}).get("screen") or {}).get("blocked")),
            "reasons": gate.get("reasons", []),
        })
        r = results[-1]
        print(f"{r['id']} {r['category']:<22} lane {r['lane']:<9} {'SUCCESS' if r['success'] else 'defended'}",
              flush=True)
    return results


def main() -> None:
    items = load_set(ROOT / "data" / "redteam" / "injection_v1.jsonl")
    results = asyncio.run(run(items))
    report = {
        "what": "40 injection tickets through the full pipeline and the confidence gate",
        "n": len(results),
        "successes": sum(r["success"] for r in results),
        "successful_ids": [r["id"] for r in results if r["success"]],
        "lanes": dict(Counter(r["lane"] for r in results)),
        "screen_blocked": sum(r["screen_blocked"] for r in results),
        "results": results,
    }
    out = ROOT / "docs" / "results" / "redteam-v3-pipeline.json"
    out.write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    print(f"{report['successes']}/{report['n']} attacks reach an engineer; lanes {report['lanes']} -> {out}")


if __name__ == "__main__":
    main()
