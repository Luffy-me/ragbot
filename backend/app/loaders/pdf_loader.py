import logging
import re
from typing import List, Optional, Tuple

import fitz  # PyMuPDF

logger = logging.getLogger(__name__)


def clean_text(text: str) -> str:
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_pdf_pages(file_path: str) -> List[Tuple[int, str]]:
    """Extract text per page. Returns list of (page_number, text)."""
    pages: List[Tuple[int, str]] = []
    with fitz.open(file_path) as doc:
        for index, page in enumerate(doc):
            page_number = index + 1
            text = page.get_text("text") or ""
            text = clean_text(text)
            if not text:
                text = _ocr_page_fallback(page)
            if text:
                pages.append((page_number, text))
    return pages


def _ocr_page_fallback(page: fitz.Page) -> str:
    """
    Lightweight OCR fallback using PyMuPDF's built-in OCR when available.
    Falls back to empty string if OCR is unavailable so indexing can continue.
    """
    try:
        textpage = page.get_textpage_ocr(language="eng", dpi=200, full=True)
        text = page.get_text("text", textpage=textpage) or ""
        return clean_text(text)
    except Exception as exc:  # noqa: BLE001
        logger.warning("OCR fallback unavailable for page %s: %s", page.number + 1, exc)
        return ""


def extract_document(file_path: str) -> List[Tuple[Optional[int], str]]:
    if not file_path.lower().endswith(".pdf"):
        raise ValueError("Only PDF files are supported in this MVP")
    pages = extract_pdf_pages(file_path)
    if not pages:
        raise ValueError("No extractable text found in the PDF")
    return [(page, text) for page, text in pages]
