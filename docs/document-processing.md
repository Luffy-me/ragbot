# Document processing notes

## MVP extractors

Primary extraction uses **PyMuPDF** (`fitz`):

1. Native text extraction per page
2. Built-in OCR fallback via `page.get_textpage_ocr(...)` when a page has no text layer

This covers the majority of official university PDFs (digital and scanned) without pulling multi-GB OCR runtimes into the default image.

## Optional extensions

The loader boundary (`app/loaders`) is intentionally small so these can be added later without API changes:

- **Unstructured** for mixed layout / table-heavy PDFs
- **PaddleOCR** for stronger multilingual OCR

Suggested integration point: wrap alternative backends behind `load_pages(file_path)` in `app/loaders/__init__.py`.
