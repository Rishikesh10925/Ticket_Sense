# OCR and attachment-text extraction: quality notes

Week 7 note (Shivaganesh) evaluating `ai/ocr/extract.py` — EasyOCR for image
attachments, `pypdf` for PDF text-layer extraction, and plain reads for log/text
files — against the hand-crafted sample screenshots in `data/sample_screenshots/`.

## No real screenshots are available

Like the synthetic labeled tickets (Week 4) and synthetic resolved tickets (Week 5),
there is no real corpus of user-submitted screenshots to evaluate against. The five
sample images in `data/sample_screenshots/` are hand-crafted with Pillow
(`data/make_sample_screenshots.py`, see `data/README.md`) to resemble real failure
modes for each department: a Windows VPN error dialog,
an SAP purchase-order-blocked screen, a dark-terminal Postgres connection error, an HR
portal failure message, and a dark AWS-console access-denied error. This is an honest
stand-in, not real data — treat the numbers below as evidence the pipeline works and a
first read of EasyOCR's error patterns, not a validated accuracy measurement.

## Results

| Sample | Style | Confidence | Extraction time |
|---|---|---|---|
| `sap_po_blocked.png` | Light dialog, sans-serif | 0.944 | 1.0s |
| `networking_vpn_error.png` | Light dialog, sans-serif | 0.935 | 0.9s |
| `database_connection_error.png` | Dark terminal, monospace | 0.921 | 1.2s |
| `hr_payslip_failure.png` | Light dialog, sans-serif | 0.893 | 0.9s |
| `cloud_access_denied.png` | Dark console, mixed font | 0.808 | 35.1s* |

\* First call only — EasyOCR downloads and loads its detection/recognition model
weights once per process (lazy singleton, same pattern as
`ai/embeddings/retrieve.py`'s `SentenceTransformer`), not once per ticket. Every
subsequent extraction in the same backend process runs in ~1s.

All five samples produced substantially correct, usable text — every one preserves
enough of the original message that a reader (or the retrieval/draft pipeline
downstream) can tell what the ticket is about. Confidence tracked actual quality: the
lowest-confidence sample (`cloud_access_denied.png`, 0.808) also had the most
character-level errors.

## Known limitations, read directly off these five samples

- **Reversed contrast (light text on dark background) is the weak point.** Both dark
  samples score lower than the three light ones, and `cloud_access_denied.png` is
  clearly the worst: `s3:GetObject` came back as `53:Getobject`, and
  `arn:aws:s3:::finance-reports/aug-2026.csv` came back badly fragmented
  (`arn:aws:53:.` / `:finance-` / `eports/aug-2026.cSv`, dropping the leading `r` off
  "resource" entirely). The terminal sample (also dark, but plain monospace rather
  than a styled console with an icon/logo) held up much better (0.921), so the
  compounding factor looks like "dark + stylized UI chrome," not dark backgrounds on
  their own.
- **Punctuation and lookalike characters get confused.** Commas were repeatedly read
  as semicolons ("time; or there was" instead of "time, or there was"); a period after
  "08/2026" became an underscore; `max_connections=100` came back as
  `max_connections-100` (`=` misread as `-`); `5th` came back as `Sth`. None of these
  change the meaning enough to matter for classification or retrieval, but they'd
  break anything doing exact string matching on the extracted text.
- **Long lines get broken into fragments.** EasyOCR's line-level detection sometimes
  splits one visual line into several detections in the middle of a word or phrase
  ("no identity-based policy allows\nthis action-" reads fine; "resource\narn:aws:s3:"
  reads worse) — `extract_from_image()` joins every detection with `\n`, so a
  downstream reader sees more line breaks than the original text actually had. This
  doesn't lose information, just reformats it.
- **PDF and log extraction have no comparable failure mode** — `pypdf` reads an
  embedded text layer directly (not OCR), so `cloud_quota_report.pdf` and
  `app_error.log` extracted with zero errors and `confidence=1.0` (see
  `backend/tests/test_ocr_extract.py`). The one real limitation there is a **scanned
  (image-only) PDF**, which has no text layer for `pypdf` to find — `extract_from_pdf`
  reports that the same way as an empty OCR read (`confidence=None`), not as an error,
  since there's nothing wrong with the extraction itself. Nothing in this project
  exercises that path yet (no scanned-PDF sample), so it's a documented gap, not a
  tested one.

## What this means for the confidence model (Weeks 8–11)

`ocr_confidence` is wired into `Ticket.confidence_features` (see
[langgraph-pipeline.md](langgraph-pipeline.md)) specifically because these numbers
already show it's informative: the sample with the most extraction errors also has the
lowest score. A future confidence model can use it as a real signal — a ticket whose
attachment OCR came back at 0.80 is more likely to have a garbled `attachment_text`
than one at 0.94 — without needing OCR itself to ever "decide" how confident the
overall draft should be.
