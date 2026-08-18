from fastapi import APIRouter
from sqlalchemy import text

from app.config import get_settings
from app.database import engine
from app.rag.llm import nvidia_client
from app.schemas import HealthResponse

router = APIRouter(tags=["health"])
settings = get_settings()


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    db_status = "ok"
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception:  # noqa: BLE001
        db_status = "unavailable"

    nvidia_status = "ok" if await nvidia_client.health() else "unavailable"
    overall = "ok" if db_status == "ok" and nvidia_status == "ok" else "degraded"

    return HealthResponse(
        status=overall,
        app=settings.app_name,
        database=db_status,
        nvidia=nvidia_status,
        embedding_model=settings.embedding_model,
    )
