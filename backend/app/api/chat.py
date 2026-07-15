import json
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal, get_db
from app.models import User
from app.rag.llm import ollama_client
from app.schemas import ChatHistoryItem, ChatRequest
from app.security.deps import get_current_user
from app.services.chat import chat_service

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("")
async def chat(
    payload: ChatRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    question = payload.question.strip()
    if not question:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question cannot be empty",
        )

    if not payload.stream:
        return await chat_service.answer(db, user, question)

    _, citations, context_blocks = await chat_service.prepare_stream(db, question)
    user_id = user.id

    async def event_stream():
        yield f"data: {json.dumps({'type': 'citations', 'citations': [c.model_dump() for c in citations]})}\n\n"
        answer_parts: list[str] = []
        async for token in ollama_client.stream_generate(question, context_blocks):
            answer_parts.append(token)
            yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"

        answer = "".join(answer_parts).strip()
        async with AsyncSessionLocal() as session:
            history = await chat_service.save_exchange(
                session, user_id, question, answer, citations
            )
        yield f"data: {json.dumps({'type': 'done', 'conversation_id': history.id})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/history", response_model=List[ChatHistoryItem])
async def chat_history(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[ChatHistoryItem]:
    return await chat_service.history(db, user)
