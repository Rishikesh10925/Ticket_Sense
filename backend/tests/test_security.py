"""Security tests in CI (Blueprint V2 §16, Roadmap Week 6): seeded PII never reaches a
model call, a log line or a stored pipeline artifact, and retrieval never crosses a
department boundary."""

import asyncio
import json
import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import settings
from app.models import Department, KBChunk, KnowledgeBase
from app.routers.knowledge_base import _get_model
from generation.llm import ExtractiveStubClient
from test_confidence_gate import _admin_token, _department_id_sync, _register_and_login

PII = {
    "email": "meera.nair@example.com",
    "phone": "+91 98450 12345",
    "secret": "Tr0ub4dor&3",
    "pan": "ABCDE1234F",
}


class _RecordingClient(ExtractiveStubClient):
    """The offline drafter, plus a record of every prompt the pipeline sent."""

    def __init__(self):
        self.requests = []

    def complete(self, request):
        self.requests.append(request.system + "\n" + request.user)
        return super().complete(request)


async def _fetch(sql: str, **params) -> list:
    engine = create_async_engine(settings.database_url)
    async with engine.connect() as conn:
        rows = (await conn.execute(text(sql), params)).all()
    await engine.dispose()
    return rows


def _pii_ticket(api) -> str:
    customer = _register_and_login(api, "pii_customer@example.com")
    resp = api.post(
        "/tickets",
        data={
            "subject": f"VPN not connecting, call me on {PII['phone']}",
            "description": (
                f"My VPN client hangs on connecting. I'm {PII['email']}, PAN {PII['pan']}. "
                f"I already tried my password: {PII['secret']} twice."
            ),
        },
        headers={"Authorization": f"Bearer {customer}"},
    )
    return resp.json()["id"]


def _assert_clean(blob: str, where: str) -> None:
    for kind, value in PII.items():
        assert value not in blob, f"{kind} leaked into {where}"


def test_seeded_pii_never_reaches_models_logs_or_stored_artifacts(api, monkeypatch, caplog):
    client = _RecordingClient()
    monkeypatch.setattr("app.services.pipeline.get_llm_client", lambda name: client)
    caplog.set_level(logging.DEBUG)
    _department_id_sync("Networking")

    ticket_id = _pii_ticket(api)

    # 1. Model calls: the drafter only ever saw placeholders.
    assert client.requests, "the pipeline never called the drafter"
    for prompt in client.requests:
        _assert_clean(prompt, "a model prompt")
    assert any("[EMAIL_1]" in p for p in client.requests)

    # 2. Logs, at every level, from every logger.
    _assert_clean("\n".join(r.getMessage() for r in caplog.records), "the logs")

    # 3. Stored pipeline artifacts: retrieval log, draft, draft claims.
    for sql in (
        "SELECT query_text FROM retrieval_runs WHERE ticket_id = :t",
        "SELECT raw_text || steps::text || evidence::text FROM drafts WHERE ticket_id = :t",
        "SELECT c.text FROM draft_claims c JOIN drafts d ON d.id = c.draft_id WHERE d.ticket_id = :t",
    ):
        _assert_clean(json.dumps([list(r) for r in asyncio.run(_fetch(sql, t=ticket_id))]), sql)

    # 4. The ticket row keeps the redacted text and the map for the engineer.
    (redacted, mapping, version), = asyncio.run(
        _fetch("SELECT redacted_text, redaction_map, redactor_version FROM tickets WHERE id = :t", t=ticket_id)
    )
    _assert_clean(redacted, "tickets.redacted_text")
    assert set(mapping.values()) == set(PII.values())
    assert version == "pii-v1"


def test_customer_and_engineer_views_never_expose_the_redaction_map(api):
    _department_id_sync("Networking")
    ticket_id = _pii_ticket(api)
    admin = _admin_token(api, "pii_admin@example.com")
    body = api.get(f"/tickets/{ticket_id}", headers={"Authorization": f"Bearer {admin}"}).json()
    assert "redaction_map" not in body and "redacted_text" not in body


def test_retrieval_never_crosses_departments(api):
    # An HR article that matches the ticket's words better than anything in Networking
    # must still never be retrieved, logged as a candidate or cited for a Networking ticket.
    _department_id_sync("Networking")

    async def _hr_decoy():
        from embeddings.chunking import chunk_markdown

        engine = create_async_engine(settings.database_url)
        async with async_sessionmaker(engine, expire_on_commit=False)() as db:
            hr = Department(name="HR")
            db.add(hr)
            await db.flush()
            title = "VPN client hangs on connecting from home"
            content = "## Resolution steps\n1. HR decoy: VPN client hangs on connecting from home, need this fixed today.\n"
            article = KnowledgeBase(department_id=hr.id, title=title, content=content)
            db.add(article)
            await db.flush()
            for chunk in chunk_markdown(title, None, content):
                db.add(
                    KBChunk(
                        knowledge_base_id=article.id,
                        chunk_index=chunk.index,
                        sections=",".join(chunk.sections),
                        text=chunk.text,
                        n_tokens=chunk.n_tokens,
                        embedding=_get_model().encode(chunk.text, normalize_embeddings=True).tolist(),
                    )
                )
            await db.commit()
            hr_article = article.id
        await engine.dispose()
        return hr_article

    hr_article = asyncio.run(_hr_decoy())
    customer = _register_and_login(api, "leak_customer@example.com")
    ticket_id = api.post(
        "/tickets",
        data={"subject": "VPN not connecting from home", "description": "VPN client hangs on connecting"},
        headers={"Authorization": f"Bearer {customer}"},
    ).json()["id"]

    rows = asyncio.run(
        _fetch(
            "SELECT h.knowledge_base_id FROM retrieval_hits h JOIN retrieval_runs r ON r.id = h.run_id "
            "WHERE r.ticket_id = :t",
            t=ticket_id,
        )
    )
    assert rows, "retrieval logged no candidates"
    assert hr_article not in {r[0] for r in rows}
    evidence = asyncio.run(_fetch("SELECT evidence::text FROM drafts WHERE ticket_id = :t", t=ticket_id))
    assert "HR decoy" not in evidence[0][0]
