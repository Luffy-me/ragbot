import logging
from dataclasses import dataclass
from typing import List, Optional

from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.embeddings.service import embedding_service
from app.loaders.pdf_loader import extract_document
from app.models import Document, DocumentChunk, DocumentStatus, utcnow
from app.rag.chunking import TextChunk, split_pages_into_chunks
from app.schemas import Citation

logger = logging.getLogger(__name__)


@dataclass
class RetrievedChunk:
    chunk_id: str
    document_id: str
    document_name: str
    page: Optional[int]
    text: str
    score: float


class RAGService:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def index_document(self, db: AsyncSession, document_id: str) -> None:
        result = await db.execute(select(Document).where(Document.id == document_id))
        document = result.scalar_one_or_none()
        if document is None:
            logger.error("Document %s not found for indexing", document_id)
            return

        document.status = DocumentStatus.INDEXING.value
        document.error_message = None
        await db.commit()

        try:
            pages = extract_document(document.stored_path)
            chunks = split_pages_into_chunks(
                pages,
                chunk_size=self.settings.chunk_size,
                chunk_overlap=self.settings.chunk_overlap,
            )
            if not chunks:
                raise ValueError("No chunks produced from document")

            await db.execute(
                delete(DocumentChunk).where(DocumentChunk.document_id == document.id)
            )

            embeddings = await embedding_service.embed_texts([c.text for c in chunks])
            for chunk, vector in zip(chunks, embeddings, strict=True):
                db.add(
                    DocumentChunk(
                        document_id=document.id,
                        page=chunk.page,
                        chunk_index=chunk.chunk_index,
                        chunk=chunk.text,
                        embedding=vector,
                    )
                )

            document.page_count = len({p for p, _ in pages if p is not None})
            document.chunk_count = len(chunks)
            document.status = DocumentStatus.READY.value
            document.indexed_at = utcnow()
            document.error_message = None
            await db.commit()
            logger.info(
                "Indexed document %s (%s chunks)", document.filename, document.chunk_count
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to index document %s", document_id)
            await db.rollback()
            result = await db.execute(select(Document).where(Document.id == document_id))
            document = result.scalar_one()
            document.status = DocumentStatus.FAILED.value
            document.error_message = str(exc)[:2000]
            await db.commit()

    async def reindex_all(self, db: AsyncSession) -> List[str]:
        result = await db.execute(select(Document).order_by(Document.uploaded_at.desc()))
        documents = result.scalars().all()
        ids = [doc.id for doc in documents]
        for doc_id in ids:
            await self.index_document(db, doc_id)
        return ids

    async def retrieve(self, db: AsyncSession, question: str) -> List[RetrievedChunk]:
        query_vector = await embedding_service.embed_query(question)
        vector_literal = "[" + ",".join(str(float(x)) for x in query_vector) + "]"

        sql = text(
            """
            SELECT
                c.id AS chunk_id,
                c.document_id AS document_id,
                d.filename AS document_name,
                c.page AS page,
                c.chunk AS chunk_text,
                1 - (c.embedding <=> CAST(:query_embedding AS vector)) AS score
            FROM document_chunks c
            JOIN documents d ON d.id = c.document_id
            WHERE d.status = 'ready'
            ORDER BY c.embedding <=> CAST(:query_embedding AS vector)
            LIMIT :top_k
            """
        )
        rows = (
            await db.execute(
                sql,
                {
                    "query_embedding": vector_literal,
                    "top_k": self.settings.top_k,
                },
            )
        ).mappings().all()

        retrieved: List[RetrievedChunk] = []
        for row in rows:
            score = float(row["score"] or 0.0)
            if score < self.settings.similarity_threshold:
                continue
            retrieved.append(
                RetrievedChunk(
                    chunk_id=str(row["chunk_id"]),
                    document_id=str(row["document_id"]),
                    document_name=str(row["document_name"]),
                    page=row["page"],
                    text=str(row["chunk_text"]),
                    score=score,
                )
            )
        return retrieved

    def build_context_blocks(self, chunks: List[RetrievedChunk]) -> List[str]:
        blocks: List[str] = []
        for index, chunk in enumerate(chunks, start=1):
            page_label = f"page {chunk.page}" if chunk.page is not None else "page unknown"
            blocks.append(
                f"[{index}] Source: {chunk.document_name} ({page_label})\n{chunk.text}"
            )
        return blocks

    def to_citations(self, chunks: List[RetrievedChunk]) -> List[Citation]:
        citations: List[Citation] = []
        for chunk in chunks:
            excerpt = chunk.text[:280] + ("…" if len(chunk.text) > 280 else "")
            citations.append(
                Citation(
                    document_id=chunk.document_id,
                    document_name=chunk.document_name,
                    page=chunk.page,
                    chunk_id=chunk.chunk_id,
                    excerpt=excerpt,
                    score=round(chunk.score, 4),
                )
            )
        return citations


rag_service = RAGService()
