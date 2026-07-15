from typing import List, Optional, Tuple

from app.loaders.pdf_loader import extract_document, extract_pdf_pages

__all__ = ["extract_document", "extract_pdf_pages", "PageText"]

PageText = Tuple[Optional[int], str]


def load_pages(file_path: str) -> List[PageText]:
    """Public loader entrypoint used by the indexing pipeline."""
    return extract_document(file_path)
