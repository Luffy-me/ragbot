import asyncio
import logging
from typing import List, Optional

import numpy as np
import torch
from sentence_transformers import SentenceTransformer

from app.config import get_settings

logger = logging.getLogger(__name__)


def _assert_safe_torch() -> None:
    version = torch.__version__.split("+")[0]
    major, minor, *_ = [int(p) for p in version.split(".")]
    if (major, minor) < (2, 6):
        raise RuntimeError(
            f"torch {torch.__version__} is too old for embedding model load "
            "(need >= 2.6 for CVE-2025-32434). Rebuild the backend image with "
            "`docker compose build --no-cache backend`."
        )


class EmbeddingService:
    """Thread-safe lazy loader for BAAI/bge-m3 embeddings."""

    def __init__(self) -> None:
        self._model: Optional[SentenceTransformer] = None
        self._lock = asyncio.Lock()
        self.settings = get_settings()

    def _load_model(self) -> SentenceTransformer:
        if self._model is None:
            _assert_safe_torch()
            logger.info(
                "Loading embedding model %s (torch %s)",
                self.settings.embedding_model,
                torch.__version__,
            )
            self._model = SentenceTransformer(
                self.settings.embedding_model,
                device=self.settings.embedding_device,
            )
            logger.info("Embedding model ready")
        return self._model

    async def embed_texts(self, texts: List[str], batch_size: int = 16) -> List[List[float]]:
        if not texts:
            return []

        async with self._lock:
            model = self._load_model()

        def _encode() -> List[List[float]]:
            vectors = model.encode(
                texts,
                batch_size=batch_size,
                normalize_embeddings=True,
                show_progress_bar=False,
            )
            arr = np.asarray(vectors, dtype=np.float32)
            return arr.tolist()

        return await asyncio.to_thread(_encode)

    async def embed_query(self, query: str) -> List[float]:
        vectors = await self.embed_texts([query])
        return vectors[0]


embedding_service = EmbeddingService()
