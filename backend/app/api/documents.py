from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, File, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal, get_db
from app.models import User
from app.rag.service import rag_service
from app.schemas import DocumentOut, MessageResponse, ReindexResponse
from app.security.deps import get_current_admin
from app.services.documents import document_service

router = APIRouter(prefix="/documents", tags=["documents"])


async def _index_in_background(document_id: str) -> None:
    async with AsyncSessionLocal() as session:
        await document_service.index_document(session, document_id)


@router.get("", response_model=List[DocumentOut])
async def list_documents(
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> List[DocumentOut]:
    docs = await document_service.list_documents(db)
    return [DocumentOut.model_validate(d) for d in docs]


@router.post("/upload", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> DocumentOut:
    document = await document_service.save_upload(db, file, uploaded_by=admin.id)
    background_tasks.add_task(_index_in_background, document.id)
    return DocumentOut.model_validate(document)


@router.delete("/{document_id}", response_model=MessageResponse)
async def delete_document(
    document_id: str,
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    await document_service.delete_document(db, document_id)
    return MessageResponse(message="Document deleted")


@router.post("/reindex", response_model=ReindexResponse)
async def reindex_knowledge_base(
    background_tasks: BackgroundTasks,
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> ReindexResponse:
    docs = await document_service.list_documents(db)
    ids = [d.id for d in docs]

    async def _run() -> None:
        async with AsyncSessionLocal() as session:
            await rag_service.reindex_all(session)

    background_tasks.add_task(_run)
    return ReindexResponse(
        message="Re-indexing started for all documents",
        document_ids=ids,
    )
