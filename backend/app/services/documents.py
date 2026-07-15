import logging
from pathlib import Path
from typing import List
from uuid import uuid4

import aiofiles
from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models import Document, DocumentStatus
from app.rag.service import rag_service

logger = logging.getLogger(__name__)
settings = get_settings()

ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/x-pdf",
    "application/acrobat",
    "application/vnd.pdf",
}


class DocumentService:
    def __init__(self) -> None:
        Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)

    async def list_documents(self, db: AsyncSession) -> List[Document]:
        result = await db.execute(select(Document).order_by(Document.uploaded_at.desc()))
        return list(result.scalars().all())

    async def get_document(self, db: AsyncSession, document_id: str) -> Document:
        result = await db.execute(select(Document).where(Document.id == document_id))
        document = result.scalar_one_or_none()
        if document is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
        return document

    async def save_upload(
        self,
        db: AsyncSession,
        file: UploadFile,
        uploaded_by: str,
    ) -> Document:
        filename = Path(file.filename or "").name
        if not filename.lower().endswith(".pdf"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only PDF files are allowed",
            )

        content_type = (file.content_type or "").lower()
        if content_type and content_type not in ALLOWED_CONTENT_TYPES:
            # Some browsers send octet-stream for PDFs; allow that if extension is .pdf
            if content_type != "application/octet-stream":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unsupported content type: {content_type}",
                )

        document_id = str(uuid4())
        stored_name = f"{document_id}_{filename}"
        stored_path = str(Path(settings.upload_dir) / stored_name)

        size = 0
        async with aiofiles.open(stored_path, "wb") as out:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                if size > settings.max_upload_bytes:
                    await out.close()
                    Path(stored_path).unlink(missing_ok=True)
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"File exceeds {settings.max_upload_size_mb}MB limit",
                    )
                await out.write(chunk)

        # Validate PDF magic header
        with open(stored_path, "rb") as fh:
            header = fh.read(5)
        if header != b"%PDF-":
            Path(stored_path).unlink(missing_ok=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is not a valid PDF",
            )

        document = Document(
            id=document_id,
            filename=filename,
            stored_path=stored_path,
            file_size=size,
            status=DocumentStatus.PENDING.value,
            uploaded_by=uploaded_by,
        )
        db.add(document)
        await db.commit()
        await db.refresh(document)
        return document

    async def delete_document(self, db: AsyncSession, document_id: str) -> None:
        document = await self.get_document(db, document_id)
        path = Path(document.stored_path)
        await db.delete(document)
        await db.commit()
        path.unlink(missing_ok=True)

    async def index_document(self, db: AsyncSession, document_id: str) -> None:
        await rag_service.index_document(db, document_id)


document_service = DocumentService()
