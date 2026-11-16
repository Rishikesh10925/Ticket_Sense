"""Demo complaint portals for the browser extension (development and test only).

Stand-ins for a real organisation's complaint websites, so the extension's "open the
portal, fill the form, the user submits" flow can be demonstrated end to end without
touching a real site. Each department gets one form page at /demo-portal/{slug}. Nothing
submitted here is stored: the confirmation page only shows a reference number, in an
element marked `data-complaint-reference`, which the extension reads back.
"""

import secrets
from html import escape

from fastapi import APIRouter, Form, HTTPException
from fastapi.responses import HTMLResponse

from app.config import settings

router = APIRouter(prefix="/demo-portal", tags=["demo portal"], include_in_schema=False)

# The selectors the seed script registers for every demo portal.
DEMO_FIELD_MAP = {
    "name": "#name",
    "email": "#email",
    "ticket_ref": "#ticket_ref",
    "category": "#category",
    "priority": "#priority",
    "subject": "#subject",
    "description": "#description",
}
DEMO_REFERENCE_SELECTOR = "[data-complaint-reference]"
CATEGORIES = ("SAP", "Cloud", "Database", "HR", "Networking", "General")

_STYLE = """
:root { color-scheme: light; --ink:#1f2937; --muted:#6b7280; --line:#d1d5db; --brand:#0f766e; }
* { box-sizing: border-box; }
body { margin:0; font: 15px/1.5 system-ui, sans-serif; color:var(--ink); background:#f3f4f6; }
header { background:var(--brand); color:#fff; padding:14px 24px; }
header strong { font-size:18px; }
main { max-width:640px; margin:24px auto; background:#fff; border:1px solid var(--line);
       border-radius:10px; padding:24px; }
label { display:block; font-weight:600; margin:14px 0 4px; }
input, select, textarea { width:100%; padding:8px 10px; border:1px solid var(--line);
       border-radius:6px; font:inherit; }
textarea { min-height:140px; }
.row { display:grid; grid-template-columns:1fr 1fr; gap:12px; }
button { margin-top:20px; background:var(--brand); color:#fff; border:0; border-radius:6px;
       padding:10px 18px; font:inherit; font-weight:600; cursor:pointer; }
.note { color:var(--muted); font-size:13px; }
.ref { font-size:22px; font-weight:700; letter-spacing:.5px; }
"""


def _enabled() -> None:
    if settings.app_env not in ("development", "test"):
        raise HTTPException(status_code=404, detail="Not found")


def _title(slug: str) -> str:
    return slug.replace("-", " ").title()


def _page(title: str, body: str) -> HTMLResponse:
    return HTMLResponse(
        f"<!doctype html><html lang=en><head><meta charset=utf-8>"
        f"<meta name=viewport content='width=device-width, initial-scale=1'>"
        f"<title>{escape(title)}</title><style>{_STYLE}</style></head>"
        f"<body><header><strong>{escape(title)}</strong> · demo complaint portal</header>"
        f"<main>{body}</main></body></html>"
    )


@router.get("/{slug}", response_class=HTMLResponse)
async def portal_form(slug: str) -> HTMLResponse:
    _enabled()
    title = f"{_title(slug)} complaints"
    options = "".join(f"<option>{c}</option>" for c in CATEGORIES)
    body = f"""
<p class=note>A demo stand-in for an organisation's complaint website. Nothing you submit is stored.</p>
<form method=post>
  <div class=row>
    <div><label for=name>Your name</label><input id=name name=name required></div>
    <div><label for=email>Email</label><input id=email name=email type=email required></div>
  </div>
  <div class=row>
    <div><label for=category>Category</label><select id=category name=category>{options}</select></div>
    <div><label for=priority>Priority</label>
      <select id=priority name=priority><option>low</option><option selected>medium</option>
      <option>high</option></select></div>
  </div>
  <label for=ticket_ref>Your reference (optional)</label><input id=ticket_ref name=ticket_ref>
  <label for=subject>Subject</label><input id=subject name=subject required maxlength=255>
  <label for=description>Describe the problem</label><textarea id=description name=description required></textarea>
  <button type=submit>Submit complaint</button>
</form>"""
    return _page(title, body)


@router.post("/{slug}", response_class=HTMLResponse)
async def portal_submit(
    slug: str,
    name: str = Form(..., max_length=255),
    email: str = Form(..., max_length=255),
    subject: str = Form(..., max_length=255),
    description: str = Form(...),
    category: str = Form("General", max_length=64),
    priority: str = Form("medium", max_length=16),
    ticket_ref: str = Form("", max_length=64),
) -> HTMLResponse:
    _enabled()
    reference = f"{(slug[:3] or 'gen').upper()}-{secrets.randbelow(10**6):06d}"
    yours = f"<p>Your reference: {escape(ticket_ref)}</p>" if ticket_ref else ""
    body = f"""
<h2>Complaint received</h2>
<p>Thank you, {escape(name)}. Your complaint "{escape(subject)}" ({escape(category)}, {escape(priority)} priority)
has been registered. Updates go to {escape(email)}.</p>
<p>Complaint number</p>
<p class=ref data-complaint-reference>{reference}</p>
{yours}
<p class=note>Demo portal: this complaint was not stored or sent anywhere.</p>"""
    return _page(f"{_title(slug)} complaints", body)
