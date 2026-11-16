# TicketSense browser extension (experimental)

A Chrome extension (Manifest V3) that brings TicketSense to any page:

- **The knowledge base can answer** (gate lane fast or assisted): the cited answer is shown
  in the side panel. In the assisted lane it carries a "check before you act" warning,
  because an engineer has not reviewed it yet. The ticket still goes to the engineer queue
  in the web app as usual.
- **It cannot** (escalate lane, or the user says the answer did not help): the extension
  opens the complaint portal registered for the ticket's department, fills the form from
  the ticket, and **the user reviews it and clicks Submit**. The extension never submits a
  form on its own. When the portal shows a complaint number, the extension reads it and
  stores it on the ticket.

This is experimental work outside the evaluated system: it is not part of the
pre-registered evaluation, the paper or the report.

## Run it

1. Start TicketSense (database, API on `http://localhost:8000`, Ollama), then apply the
   migration and register the demo portals, from `backend/`:

   ```bash
   .venv/Scripts/python -m alembic upgrade head        # adds complaint_portals (0024)
   .venv/Scripts/python -m app.scripts.seed_portals    # one demo portal per department + a default
   ```

2. In Chrome, open `chrome://extensions`, turn on **Developer mode**, click **Load unpacked**
   and choose this `extension/` folder.
3. Click the TicketSense icon in the toolbar to open the side panel and sign in with an
   end-user account (demo: `customer@demo.local` / `Demo@123`).
4. Describe the problem, or select text on any page, right-click and choose
   **Ask TicketSense about "…"**.

## How it works

| File | Role |
|---|---|
| `manifest.json` | Side panel, context menu; host access to the local API only, other sites asked for when needed |
| `sidepanel.html/.css/.js` | Sign in, ask, the answer or portal view, ticket list |
| `background.js` | Opens the side panel, follows portal tabs: fills the form once loaded, then reads the reference number |
| `portal.js` | The two functions injected into the portal page: fill the form, read the reference |
| `api.js` | API client; the token is kept in session storage and cleared when the browser closes |

Backend pieces (in `backend/`):

| Endpoint | Who | Does |
|---|---|---|
| `GET /assist/tickets/{id}` | the ticket's submitter, admin | State (`processing`, `answer`, `portal`, `resolved`, `closed`), the answer and sources in the fast and assisted lanes, the portal with the form values |
| `POST /assist/tickets/{id}/portal-reference` | submitter, admin | Stores the portal's complaint number on the ticket |
| `GET/PUT /portals`, `DELETE /portals/{id}` | admin | The portal registry; also editable in the web app under **Admin → Complaint Portals** |
| `GET/POST /demo-portal/{slug}` | anyone, development only | Local demo complaint forms; nothing submitted is stored |

A portal's `field_map` links ticket fields (`subject`, `description`, `category`,
`priority`, `name`, `email`, `ticket_ref`) to CSS selectors on its form;
`reference_selector` finds the complaint number on the page shown after submitting.

## Safety rules

- The user always clicks Submit; sign-in pages and CAPTCHAs on real portals stay manual.
- Host access only to the TicketSense API by default; a portal's site is requested the
  first time the user opens it.
- Text from the API and the portal is inserted as text, never as HTML.
- The PII redaction step still runs before any model call; the original values go only
  into the form the user is looking at.

## Tested

`backend/tests/test_assist.py` covers the answer rule, portal fallback, access control,
reference storage, the admin registry and the demo pages. The full flow (sign in, ask,
answer or portal, fill, submit, reference stored) was run in Chromium with the unpacked
extension for an answered VPN ticket (assisted lane) and two escalated tickets.
