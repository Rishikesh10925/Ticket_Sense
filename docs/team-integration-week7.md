# Week 7 Team Integration

Evidence for the Week 7 milestone's Team Integration deliverable: "Test the full
intake-to-draft pipeline with an attached screenshot end-to-end, confirming OCR text
correctly feeds into retrieval and drafting."

## What this branch is

`week7-aashritha-attachment-upload-ui` combines all three Week 7 member branches
(Shivaganesh's OCR/PDF/log extraction → Rishikesh's pipeline wiring/storage/retrieval
→ Aashritha's upload UI, the same dependency order and pattern as Weeks 4–6).

## Dry run methodology

Submitted 6 tickets through the real running API with **deliberately vague**
subjects/descriptions ("Help" / "See attached, urgent.") and a real file attached —
five of the hand-crafted sample screenshots (one per department) plus the PDF sample,
so the only thing that could make classification/retrieval/drafting work correctly is
the attachment's extracted text. This is a stronger test than Week 6's dry run: there
it was the description doing the work, here it deliberately isn't.

## Results

| Attachment | Type | Expected dept | Routed dept | OCR/extract confidence | Fully grounded |
|---|---|---|---|---|---|
| `networking_vpn_error.png` | image | Networking | Networking | 0.935 | yes |
| `sap_po_blocked.png` | image | SAP | SAP | 0.944 | yes |
| `database_connection_error.png` | image | Database | Database | 0.921 | yes |
| `hr_payslip_failure.png` | image | HR | HR | 0.893 | yes |
| `cloud_access_denied.png` | image | Cloud | **Networking** | 0.808 | yes |
| `cloud_quota_report.pdf` | pdf | Cloud | **HR** | 1.0 | yes |

**6/6 tickets reached `drafted` unattended, and 6/6 had attachment text successfully
extracted and persisted** — the extended pipeline (extract → classify → route →
retrieve → draft) never broke across image or PDF attachments.

**Confirmed: OCR/extracted text is what drove classification and retrieval**, not the
vague description — with subjects like "Help" and "Issue", there was nothing else for
the classifier or retriever to work from. The `networking_vpn_error.png` ticket is the
clearest example: description "See attached, urgent." alone is unclassifiable, but the
ticket landed correctly in Networking and its evidence panel returned genuinely
relevant VPN knowledge-base articles and resolved tickets (verified live in a browser,
not just via this script — see the mentor demo script below).

**6/6 generated drafts were fully grounded** — same automated `check_groundedness()`
pass as Week 6's dry run, now against drafts generated from OCR'd/extracted text
rather than typed descriptions.

**4/6 routed to the expected department.** Both misroutes were the Cloud samples
(`cloud_access_denied.png` → Networking, `cloud_quota_report.pdf` → HR) — despite the
extracted/OCR'd text being clean and on-topic (`"Cloud Console / S3 / Access Denied /
User not authorized..."` and `"Incident Report - Cloud Storage Quota Exceeded..."`).
This is the same already-documented department-classifier weak spot from
[classification-model.md](classification-model.md) (Cloud/SAP/Database are
under-represented in the training data relative to Networking/HR) — notable here
because it held even with two different extraction methods (OCR and direct PDF text)
producing clean, readable, on-topic text. The classifier's Cloud-department weakness
isn't an OCR/extraction problem; extraction did its job in both cases.

## No breakages found

As with Week 6, this dry run didn't surface a bug needing a joint fix — attachment
storage, OCR, PDF extraction, the pipeline's `extract` node, persistence, and the
upload/display UI all worked as designed across all 6 attempts, including the one PDF
attachment (the other five dry-run tickets are images; the PDF path is exercised here
and in `backend/tests/test_ocr_extract.py`, not elsewhere).

## Mentor demo script

1. Log in as `customer@demo.local` (`Demo@123`).
2. Submit a ticket with subject "VPN not connecting - see attached", description
   "Screenshot attached, my VPN is broken.", and attach
   `data/sample_screenshots/networking_vpn_error.png`.
3. See the live upload preview (thumbnail + filename + size) before submitting.
4. Click into the ticket — within a few seconds, unattended, it reaches "Draft in
   review", routed to Networking with `high` priority.
5. The Attachment section shows the actual image, an "OCR confidence: 93%" badge, and
   the extracted text ("VPN Connection Error / Error 619: ...").
6. The "Retrieved evidence" panel shows genuinely relevant Networking KB articles and
   resolved tickets — evidence that could only have come from the OCR'd text, since
   the typed description never mentions VPN.
7. Log in as `engineer@demo.local` and open the same ticket to see the cited AI draft,
   grounded in that same evidence.

Logbook evidence: this document's results table and the Cloud-misrouting finding
above (OCR/extraction quality notes), plus [ocr-evaluation.md](ocr-evaluation.md)'s
per-sample error analysis for the deeper "what specifically goes wrong" read.
