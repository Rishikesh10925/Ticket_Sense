"""Generates the hand-crafted sample "screenshots" in data/sample_screenshots/ used
by docs/ocr-evaluation.md and backend/tests/test_ocr_extract.py. No real user
screenshots exist for this project (same honest-substitute situation as the synthetic
labeled tickets and synthetic resolved tickets), so these are built with Pillow to
resemble real failure modes per department, styled the way each would actually appear
on screen: a Windows error dialog, an SAP screen, a dark terminal, a browser portal
message, and a dark cloud console. Re-run this to regenerate the PNGs if they're ever
deleted — the committed files are the actual test fixtures, this script isn't a
runtime dependency of anything.

Usage: uv run --project backend python data/make_sample_screenshots.py
Requires Windows fonts (Segoe UI, Consolas) available at the path below; adjust
FONT_DIR if running elsewhere.
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT_DIR = Path(__file__).resolve().parent / "sample_screenshots"
FONT_DIR = Path("C:/Windows/Fonts")


def _font(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_DIR / name), size)


def vpn_error_dialog() -> None:
    img = Image.new("RGB", (620, 260), "#f0f0f0")
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 619, 259], outline="#a0a0a0", width=2)
    d.rectangle([0, 0, 619, 36], fill="#0a5dc2")
    d.text((12, 8), "Network Connections", font=_font("segoeui.ttf", 16), fill="white")
    d.text((24, 60), "VPN Connection Error", font=_font("segoeuib.ttf", 18), fill="#202020")
    d.text(
        (24, 100),
        "Error 619: The remote computer did not respond in time,\n"
        "or there was a failure in the network. Please try to\n"
        "reconnect. If the problem continues, contact your\n"
        "network administrator.",
        font=_font("segoeui.ttf", 14),
        fill="#303030",
    )
    d.rectangle([500, 210, 596, 240], outline="#808080")
    d.text((530, 217), "Retry", font=_font("segoeui.ttf", 14), fill="#202020")
    img.save(OUT_DIR / "networking_vpn_error.png")


def sap_po_blocked() -> None:
    img = Image.new("RGB", (640, 220), "#eef1f5")
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 639, 34], fill="#354a5f")
    d.text((12, 8), "SAP Easy Access - Purchase Order", font=_font("segoeui.ttf", 15), fill="white")
    d.text((20, 55), "Purchase order 4500019873 blocked for release", font=_font("segoeuib.ttf", 16), fill="#1a1a1a")
    d.text(
        (20, 90),
        "Message no. ME 021\n\n"
        "Diagnosis: The purchase order exceeds the release\n"
        "value limit for your purchasing group and requires\n"
        "approval before it can be processed further.",
        font=_font("consola.ttf", 13),
        fill="#333333",
    )
    img.save(OUT_DIR / "sap_po_blocked.png")


def database_terminal_error() -> None:
    img = Image.new("RGB", (640, 200), "#0c0c0c")
    d = ImageDraw.Draw(img)
    font = _font("consola.ttf", 14)
    lines = [
        "$ psql -h prod-db-01 -U app_user ticketsense",
        "psql: error: connection to server failed:",
        "FATAL:  sorry, too many clients already",
        "ERROR:  connection pool exhausted (max_connections=100)",
        "HINT:   increase max_connections or reduce app pool size",
    ]
    y = 16
    for line in lines:
        color = "#ff5c57" if line.startswith(("psql: error", "FATAL", "ERROR")) else "#e0e0e0"
        d.text((16, y), line, font=font, fill=color)
        y += 26
    img.save(OUT_DIR / "database_connection_error.png")


def hr_payslip_message() -> None:
    img = Image.new("RGB", (600, 240), "#ffffff")
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 599, 44], fill="#f6f6f6")
    d.rectangle([0, 44, 599, 45], fill="#d0d0d0")
    d.text((16, 12), "HR Self-Service Portal", font=_font("segoeuib.ttf", 16), fill="#202020")
    d.text((16, 70), "Payslip generation failed", font=_font("segoeuib.ttf", 15), fill="#b00020")
    d.text(
        (16, 100),
        "We were unable to generate your payslip for the period\n"
        "08/2026. This has been logged automatically. If this\n"
        "persists past the 5th of the month, please contact HR\n"
        "support with your employee ID.",
        font=_font("segoeui.ttf", 13),
        fill="#303030",
    )
    img.save(OUT_DIR / "hr_payslip_failure.png")


def cloud_access_denied() -> None:
    img = Image.new("RGB", (660, 220), "#232f3e")
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 659, 36], fill="#161e2d")
    d.text((12, 8), "Cloud Console - S3", font=_font("segoeui.ttf", 15), fill="#ffffff")
    d.text((20, 60), "Access Denied", font=_font("segoeuib.ttf", 18), fill="#ff9900")
    d.text(
        (20, 95),
        "User is not authorized to perform s3:GetObject on\n"
        "resource arn:aws:s3:::finance-reports/aug-2026.csv\n"
        "because no identity-based policy allows this action.",
        font=_font("consola.ttf", 13),
        fill="#e8e8e8",
    )
    img.save(OUT_DIR / "cloud_access_denied.png")


def cloud_quota_report_pdf() -> None:
    from fpdf import FPDF

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "Incident Report - Cloud Storage Quota Exceeded", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 11)
    pdf.ln(4)
    pdf.multi_cell(
        0,
        7,
        "Ticket reference: INC-20894\n"
        "Reported: 2026-08-30 09:14\n\n"
        "Summary: The finance-reports S3 bucket has exceeded its allocated storage "
        "quota of 500GB. New uploads are being rejected with a QuotaExceededException. "
        "The nightly backup job failed as a result.\n\n"
        "Requested action: Increase the bucket quota to 750GB or archive objects "
        "older than 180 days to Glacier storage.",
    )
    pdf.output(str(OUT_DIR / "cloud_quota_report.pdf"))


def app_error_log() -> None:
    (OUT_DIR / "app_error.log").write_text(
        "2026-08-30T09:12:01Z INFO  app.worker: starting nightly backup job\n"
        "2026-08-30T09:12:04Z ERROR app.storage: PutObject failed for finance-reports/aug-2026.csv\n"
        "2026-08-30T09:12:04Z ERROR app.storage: QuotaExceededException: bucket quota "
        "of 500GB exceeded (current usage: 512.3GB)\n"
        "2026-08-30T09:12:04Z WARN  app.worker: backup job aborted after 1 failed upload\n"
        "2026-08-30T09:12:05Z INFO  app.worker: job finished with status=FAILED\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    vpn_error_dialog()
    sap_po_blocked()
    database_terminal_error()
    hr_payslip_message()
    cloud_access_denied()
    cloud_quota_report_pdf()
    app_error_log()
    print("wrote sample screenshots + PDF + log to", OUT_DIR)
