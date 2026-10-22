# 8. Security and responsible AI

*Owner: Rishikesh. Draft v1.*

## 8.1 Threats

The main threat is prompt injection: instructions hidden in a ticket or attachment that make
the model insert a phishing link, a destructive command or a policy override, while still
citing a real passage so the schema check passes.

## 8.2 Defences

- **Redaction** of personal data before any model call.
- **Structured drafting**: steps must cite passages; uncited or schema-invalid drafts are
  never shown.
- **Output screen** (`ai/security/output_screen.py`, screen-v2): a step is blocked if it
  contains a URL, a code-like token or a shell, cloud or SQL command that its cited
  passages do not contain, or that the passages mention only in their Warnings section.
- **The gate**: a blocked draft escalates; so does a draft the shift guard flags.
- **Access control**: role checks on every endpoint; research accounts (annotator,
  participant) cannot open real tickets (tested).

## 8.3 Red team

40 injection tickets in 21 categories, including instructions hidden in attachments (5),
direct overrides, tag breakouts, phishing links, destructive commands, credential and data
exfiltration, fake approvals, role-play, multilingual and encoded payloads, and homoglyphs
(`data/redteam/injection_v1.jsonl`):

| Run | Success (forbidden content reaches an engineer) |
|---|---|
| v1: draft-v1, no screen | 5 of 40 (12.5%) |
| v2: draft-v2 + screen-v1, drafting only | 0 of 40 |
| v3: full pipeline and gate, screen-v2 | **0 of 40**; lanes: 12 assisted, 28 escalated |

The full-pipeline run found one issue the component test missed (RT-10: a term the evidence
only warns against), fixed by screen-v2.

## 8.4 Cost of the screen

On the full benchmark screen-v2 blocks 87 of 1,484 shown drafts, 47 of which the judge
rated acceptable but which contain commands not in the cited evidence. Kept on purpose:
an engineer can still answer those tickets, and a command the evidence does not contain is
exactly what an injection would add.

## 8.5 Responsible AI

- Synthetic data only; no real personal data. Reviewers and participants are pseudonymous.
- Escalated tickets never show an AI draft; a human makes every final decision.
- [Datasheet](../datasheet.md) for the benchmark and [model card](../model-card.md) for the
  classifier and confidence model, with intended use and known failure modes.

## 8.6 Dependency and secret checks (Week 11, 2026-10-22)

| Check | Finding | Action |
|---|---|---|
| `npm audit` (frontend) | Production dependencies: 0. Dev only: vite 8.2.0 to 8.2.2 and source-map-js, high (dev-server issues) | `npm audit fix`; 0 remaining |
| `pip-audit` (backend, all 112 installed packages) | Known vulnerabilities in pyjwt 2.13.0 (login tokens), pypdf 6.16.2 (PDF attachments), pillow 12.3.0, urllib3 2.7.0, certifi, setuptools | Upgraded to pyjwt 2.15.1, pypdf 6.21.2, pillow 13.0.0, urllib3 2.8.0, certifi 2026.10.19, setuptools 84.2.1; minimum versions raised for the two direct dependencies |
| Secret scan of the full git history (cloud keys, GitHub and API tokens, private keys) | None found; only `.env.example` files are tracked | none |
| JWT secret default | The app would start in production with a public default signing key | It now refuses to start unless the secret is 32+ characters, outside development and tests |
