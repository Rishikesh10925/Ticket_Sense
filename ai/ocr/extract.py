"""Attachment text extraction: OCR for image attachments (EasyOCR), direct text
extraction for PDFs (pypdf) and log/text files (plain read). This is the function
ai/graph/nodes.py's extract node calls, and the retrieval/classification/draft nodes
downstream use its output to fold attachment context into the ticket's text (see
docs/langgraph-pipeline.md). See docs/ocr-evaluation.md for quality notes and known
limitations on the hand-crafted sample screenshots this was evaluated against.
"""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class ExtractionResult:
    text: str
    # 0-1 for OCR (image) extraction, where EasyOCR reports a per-detection
    # confidence we average across the page. None for PDF/log extraction — pulling
    # text out of a PDF's text layer or reading a plain-text file isn't a
    # probabilistic read, so there's no meaningful confidence score to report; a
    # consumer should treat None as "not applicable", not "unknown/low".
    confidence: float | None


_reader = None


def _get_reader():
    # Loaded once per process, same lazy-singleton pattern as
    # ai/embeddings/retrieve.py's SentenceTransformer — EasyOCR's Reader() loads
    # detection + recognition model weights, which is too slow to redo per ticket.
    global _reader
    if _reader is None:
        import easyocr

        _reader = easyocr.Reader(["en"], gpu=False)
    return _reader


def extract_from_image(path: str | Path) -> ExtractionResult:
    reader = _get_reader()
    detections = reader.readtext(str(path))
    if not detections:
        return ExtractionResult(text="", confidence=None)

    lines = [text for _, text, _ in detections]
    confidences = [float(conf) for _, _, conf in detections]
    return ExtractionResult(text="\n".join(lines), confidence=sum(confidences) / len(confidences))


def extract_from_pdf(path: str | Path) -> ExtractionResult:
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    pages = [page.extract_text() or "" for page in reader.pages]
    text = "\n".join(p for p in pages if p).strip()
    # A scanned (image-only) PDF has no text layer for pypdf to find — that's a
    # real "nothing extractable" result, not an extraction failure, so it's
    # reported the same way as an empty OCR read (confidence=None) rather than
    # raising.
    return ExtractionResult(text=text, confidence=1.0 if text else None)


def extract_from_log(path: str | Path) -> ExtractionResult:
    text = Path(path).read_text(encoding="utf-8", errors="replace").strip()
    return ExtractionResult(text=text, confidence=1.0 if text else None)


_EXTRACTORS = {
    "image": extract_from_image,
    "pdf": extract_from_pdf,
    "log": extract_from_log,
}


def extract_attachment_text(path: str | Path, attachment_type: str) -> ExtractionResult:
    extractor = _EXTRACTORS.get(attachment_type)
    if extractor is None:
        return ExtractionResult(text="", confidence=None)
    return extractor(path)
