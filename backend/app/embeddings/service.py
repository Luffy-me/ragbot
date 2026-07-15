import asyncio
import logging
from typing import List, Optional

import numpy as np
from sentence_transformers import SentenceTransformer

from app.config import get_settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Thread-safe lazy loader for BAAI/bge-m3 embeddings."""

    def __init__(self) -> None:
        self._model: Optional[SentenceTransformer] = None
        self._lock = asyncio.Lock()
        self.settings = get_settings()

    def _load_model(self) -> SentenceTransformer:
        if self._model is None:
            logger.info("Loading embedding model %s", self.settings.embedding_model)
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
