from dataclasses import dataclass
from typing import List, Optional, Tuple


@dataclass
class TextChunk:
    text: str
    page: Optional[int]
    chunk_index: int


def split_pages_into_chunks(
    pages: List[Tuple[Optional[int], str]],
    chunk_size: int = 800,
    chunk_overlap: int = 150,
) -> List[TextChunk]:
    """Split page texts into overlapping character chunks while preserving page metadata."""
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size")

    chunks: List[TextChunk] = []
    chunk_index = 0

    for page, text in pages:
        if not text:
            continue
        start = 0
        length = len(text)
        while start < length:
            end = min(start + chunk_size, length)
            piece = text[start:end].strip()
            if piece:
                chunks.append(TextChunk(text=piece, page=page, chunk_index=chunk_index))
                chunk_index += 1
            if end >= length:
                break
            start = max(0, end - chunk_overlap)

    return chunks
