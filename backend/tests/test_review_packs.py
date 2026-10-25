"""Offline review packs (Week 12): reviewers get only what /annotate shows, and returned
files are stored with the online tool's rules."""

import asyncio
import csv
import json
import re
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import settings
from app.models import AnnotationAssignment, Annotator, BenchmarkTicket, Draft, Label
from app.scripts import review_packs

FORBIDDEN = ("confidence", "score", "lane", "signal", "model", "type", "gold", "split", "overlap", "batch", "priority")


async def _assign(pseudonyms: list[str], n: int = 2) -> dict:
    engine = create_async_engine(settings.database_url)
    out = {}
    async with async_sessionmaker(engine, expire_on_commit=False)() as db:
        s = uuid.uuid4().hex[:6]
        for p in pseudonyms:
            annotator = await db.scalar(select(Annotator).where(Annotator.pseudonym == p))
            ids = []
            for i in range(n):
                t = BenchmarkTicket(id=f"P-{s}{p[-2:]}{i}", benchmark_version="test", group_id="G", subject=f"VPN {i}",
                                    body="VPN hangs.", department="Networking", priority="high", type="A",
                                    gold_articles=["NET-VPN-001"], split="calib")
                db.add(t)
                await db.flush()
                d = Draft(benchmark_ticket_id=t.id, benchmark_version="test", model="qwen2.5:7b-instruct",
                          prompt_version="draft-v2", schema_valid=True, can_answer=True,
                          steps=[{"text": "Retry from a hotspot.", "citations": [1]}], missing_information=[],
                          evidence=[{"n": 1, "article_key": "NET-VPN-001", "title": "VPN", "text": "Retry."}],
                          raw_text="{}", groundedness=0.9)
                db.add(d)
                await db.flush()
                a = AnnotationAssignment(draft_id=d.id, annotator_id=annotator.id, batch="t", overlap=True, position=i)
                db.add(a)
                await db.flush()
                ids.append(str(a.id))
            out[p] = ids
        await db.commit()
    await engine.dispose()
    return out


def _pack(path):
    return json.loads(re.search(r"const PACK = (\{.*?\});\n", path.read_text(encoding="utf-8"), re.S).group(1)
                      .replace("<\\/", "</"))


def _keys(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield k
            yield from _keys(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _keys(v)


def _csv(path, pseudonym, rows):
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["pack_id", "pseudonym", "assignment_id", "label", "reason_codes", "note", "skipped_reason",
                    "time_taken_ms"])
        for r in rows:
            w.writerow(["x", pseudonym, *r])


def test_add_export_import_round_trip(tmp_path, monkeypatch):
    monkeypatch.setattr(review_packs, "PACKS", tmp_path)
    created = asyncio.run(review_packs.add(["Asha", "Ravi"]))
    pseudonyms = [p for p, _ in created]
    assert all(re.fullmatch(r"REV-\d\d", p) for p in pseudonyms)
    names = (tmp_path / "reviewers.csv").read_text(encoding="utf-8")
    assert "Asha" in names and "Ravi" in names

    assigned = asyncio.run(_assign(pseudonyms))
    packs = asyncio.run(review_packs.export())
    first = next(p for p in packs if pseudonyms[0] in p.name)
    pack = _pack(first)
    assert [i["assignment_id"] for i in pack["items"]] == assigned[pseudonyms[0]]
    assert not set(_keys(pack)) & set(FORBIDDEN)  # blinded like /annotate

    a1, a2 = assigned[pseudonyms[0]]
    good = tmp_path / "labels_ok.csv"
    _csv(good, pseudonyms[0], [[a1, "R", "missing_step;invented_step", "two steps wrong", "", 95000],
                               [a2, "", "", "", "unreadable", 4000]])
    report = asyncio.run(review_packs.import_csv(good))
    assert report["stored"] == 2 and report["errors"] == [] and report["quick"] == 1

    async def stored():
        engine = create_async_engine(settings.database_url)
        async with async_sessionmaker(engine)() as db:
            rows = (await db.execute(select(Label).join(AnnotationAssignment)
                                     .where(AnnotationAssignment.id.in_([uuid.UUID(a1), uuid.UUID(a2)])))).scalars().all()
        await engine.dispose()
        return {(r.label, tuple(r.reason_codes), r.skipped_reason, r.time_taken_ms) for r in rows}

    assert asyncio.run(stored()) == {("R", ("missing_step", "invented_step"), None, 95000),
                                     (None, (), "unreadable", 4000)}
    assert asyncio.run(review_packs.import_csv(good))["already_labelled"] == 2  # labels are final


def test_import_rejects_the_whole_file_on_any_error(tmp_path, monkeypatch):
    monkeypatch.setattr(review_packs, "PACKS", tmp_path)
    pseudonyms = [p for p, _ in asyncio.run(review_packs.add(["Meena", "Kiran"]))]
    assigned = asyncio.run(_assign(pseudonyms, n=1))
    bad = tmp_path / "labels_bad.csv"
    _csv(bad, pseudonyms[0], [[assigned[pseudonyms[0]][0], "A", "", "", "", 60000],
                              [assigned[pseudonyms[1]][0], "A", "", "", "", 60000]])  # someone else's item
    report = asyncio.run(review_packs.import_csv(bad))
    assert report["stored"] == 0 and len(report["errors"]) == 1
    both = tmp_path / "labels_both.csv"
    _csv(both, pseudonyms[0], [[assigned[pseudonyms[0]][0], "A", "", "", "unreadable", 60000]])
    assert asyncio.run(review_packs.import_csv(both))["stored"] == 0  # label and skip together is invalid
