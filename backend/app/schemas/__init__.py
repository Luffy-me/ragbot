from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)


class UserOut(BaseModel):
    id: str
    email: EmailStr
    role: Literal["student", "admin"]
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class DocumentOut(BaseModel):
    id: str
    filename: str
    file_size: int
    status: str
    error_message: Optional[str] = None
    page_count: int
    chunk_count: int
    uploaded_at: datetime
    indexed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class Citation(BaseModel):
    document_id: str
    document_name: str
    page: Optional[int] = None
    chunk_id: str
    excerpt: str
    score: float


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    stream: bool = True


class ChatResponse(BaseModel):
    answer: str
    citations: List[Citation]
    conversation_id: Optional[str] = None


class ChatHistoryItem(BaseModel):
    id: str
    question: str
    answer: str
    citations: List[Citation] = []
    created_at: datetime

    model_config = {"from_attributes": True}


class HealthResponse(BaseModel):
    status: str
    app: str
    database: str
    ollama: str
    embedding_model: str


class MessageResponse(BaseModel):
    message: str


class ReindexResponse(BaseModel):
    message: str
    document_ids: List[str]
