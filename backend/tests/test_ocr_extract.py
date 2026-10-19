import sys
from pathlib import Path

AI_OCR_DIR = Path(__file__).resolve().parents[2] / "ai" / "ocr"
sys.path.insert(0, str(AI_OCR_DIR))

from extract import extract_attachment_text, extract_from_image, extract_from_log, extract_from_pdf  # noqa: E402

SAMPLES_DIR = Path(__file__).resolve().parents[2] / "data" / "sample_screenshots"


def test_extract_from_image_ocrs_readable_text():
    # See docs/ocr-evaluation.md for the full quality read across all five samples —
    # this just checks the extraction pipeline actually works end to end, not OCR
    # accuracy in general.
    result = extract_from_image(SAMPLES_DIR / "networking_vpn_error.png")
    assert "VPN" in result.text
    assert result.confidence is not None
    assert 0.0 < result.confidence <= 1.0


def test_extract_from_pdf_reads_text_layer():
    result = extract_from_pdf(SAMPLES_DIR / "cloud_quota_report.pdf")
    assert "Cloud Storage Quota Exceeded" in result.text
    assert result.confidence == 1.0


def test_extract_from_log_reads_plain_text():
    result = extract_from_log(SAMPLES_DIR / "app_error.log")
    assert "QuotaExceededException" in result.text
    assert result.confidence == 1.0


def test_extract_from_log_handles_empty_file(tmp_path):
    empty = tmp_path / "empty.log"
    empty.write_text("", encoding="utf-8")
    result = extract_from_log(empty)
    assert result.text == ""
    assert result.confidence is None


def test_extract_attachment_text_dispatches_by_type():
    pdf_result = extract_attachment_text(SAMPLES_DIR / "cloud_quota_report.pdf", "pdf")
    log_result = extract_attachment_text(SAMPLES_DIR / "app_error.log", "log")
    assert "Cloud Storage Quota Exceeded" in pdf_result.text
    assert "QuotaExceededException" in log_result.text


def test_extract_attachment_text_unknown_type_returns_empty():
    result = extract_attachment_text(SAMPLES_DIR / "app_error.log", "video")
    assert result.text == ""
    assert result.confidence is None
