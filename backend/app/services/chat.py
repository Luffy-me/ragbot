import json
from typing import List

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ChatHistory, User
from app.rag.llm import FALLBACK_ANSWER, nvidia_client
from app.rag.service import rag_service
from app.schemas import ChatHistoryItem, ChatResponse, Citation


class ChatService:
    async def answer(self, db: AsyncSession, user: User, question: str) -> ChatResponse:
        question = question.strip()
        if not question:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Question cannot be empty",
            )

        retrieved = await rag_service.retrieve(db, question)
        citations = rag_service.to_citations(retrieved)
        context_blocks = rag_service.build_context_blocks(retrieved)
        answer = await nvidia_client.generate(question, context_blocks)

        history = ChatHistory(
            user_id=user.id,
            question=question,
            answer=answer,
            sources_json=json.dumps([c.model_dump() for c in citations]),
        )
        db.add(history)
        await db.commit()
        await db.refresh(history)

        return ChatResponse(
            answer=answer,
            citations=citations,
            conversation_id=history.id,
        )

    async def prepare_stream(self, db: AsyncSession, question: str):
        retrieved = await rag_service.retrieve(db, question)
        citations = rag_service.to_citations(retrieved)
        context_blocks = rag_service.build_context_blocks(retrieved)
        return retrieved, citations, context_blocks

    async def save_exchange(
        self,
        db: AsyncSession,
        user_id: str,
        question: str,
        answer: str,
        citations: List[Citation],
    ) -> ChatHistory:
        history = ChatHistory(
            user_id=user_id,
            question=question,
            answer=answer or FALLBACK_ANSWER,
            sources_json=json.dumps([c.model_dump() for c in citations]),
        )
        db.add(history)
        await db.commit()
        await db.refresh(history)
        return history

    async def history(
        self, db: AsyncSession, user: User, limit: int = 50
    ) -> List[ChatHistoryItem]:
        result = await db.execute(
            select(ChatHistory)
            .where(ChatHistory.user_id == user.id)
            .order_by(ChatHistory.created_at.desc())
            .limit(limit)
        )
        items: List[ChatHistoryItem] = []
        for row in result.scalars().all():
            citations: List[Citation] = []
            if row.sources_json:
                try:
                    citations = [Citation(**c) for c in json.loads(row.sources_json)]
                except Exception:  # noqa: BLE001
                    citations = []
            items.append(
                ChatHistoryItem(
                    id=row.id,
                    question=row.question,
                    answer=row.answer,
                    citations=citations,
                    created_at=row.created_at,
                )
            )
        return items


chat_service = ChatService()
