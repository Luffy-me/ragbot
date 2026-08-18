import json
import logging
import re
from typing import AsyncIterator, List

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)

FALLBACK_ANSWER = (
    "I couldn't find reliable information in the university's official documents."
)

THINK_TAG_RE = re.compile(r"<think>[\s\S]*?</think>", re.IGNORECASE)

SYSTEM_PROMPT = """You are the University Knowledge Assistant.
Answer ONLY using the provided context excerpts from official university documents.
Rules:
1. If the context does not contain enough information, reply exactly:
I couldn't find reliable information in the university's official documents.
2. Do not invent policies, fees, dates, or requirements.
3. Be concise, clear, and helpful for students.
4. When relevant, mention which document/page the information comes from.
5. Prefer factual answers over speculation.
6. Do not include chain-of-thought or hidden reasoning tags in the answer.
"""


def sanitize_answer(text: str) -> str:
    return THINK_TAG_RE.sub("", text or "").strip()


class NvidiaClient:
    def __init__(self) -> None:
        self.settings = get_settings()

    @property
    def generate_url(self) -> str:
        return f"{self.settings.nvidia_base_url.rstrip('/')}/chat/completions"

    @property
    def models_url(self) -> str:
        return f"{self.settings.nvidia_base_url.rstrip('/')}/models"

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"******",
            "Content-Type": "application/json",
        }

    async def health(self) -> bool:
        if not self.settings.nvidia_api_key:
            return False
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(self.models_url, headers=self._headers())
                return response.status_code == 200
        except Exception:  # noqa: BLE001
            return False

    def _build_prompt(self, question: str, context_blocks: List[str]) -> str:
        context = "\n\n".join(context_blocks) if context_blocks else "(no relevant context)"
        return (
            f"Context:\n{context}\n\n"
            f"Student question: {question}\n\n"
            "Answer:"
        )

    def _payload(self, prompt: str, stream: bool) -> dict:
        return {
            "model": self.settings.nvidia_model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "stream": stream,
            "temperature": 0.1,
            "top_p": 0.9,
        }

    async def generate(self, question: str, context_blocks: List[str]) -> str:
        if not context_blocks:
            return FALLBACK_ANSWER
        if not self.settings.nvidia_api_key:
            return "NVIDIA API key is not configured. Set NVIDIA_API_KEY and retry."

        prompt = self._build_prompt(question, context_blocks)
        try:
            async with httpx.AsyncClient(timeout=self.settings.nvidia_timeout) as client:
                response = await client.post(
                    self.generate_url,
                    json=self._payload(prompt, stream=False),
                    headers=self._headers(),
                )
                response.raise_for_status()
                data = response.json()
                answer = sanitize_answer(
                    (
                        data.get("choices", [{}])[0]
                        .get("message", {})
                        .get("content", "")
                    ).strip()
                )
                return answer or FALLBACK_ANSWER
        except Exception as exc:  # noqa: BLE001
            logger.exception("NVIDIA generation failed: %s", exc)
            return (
                "The language model is temporarily unavailable. "
                "Please try again in a moment."
            )

    async def stream_generate(
        self, question: str, context_blocks: List[str]
    ) -> AsyncIterator[str]:
        if not context_blocks:
            yield FALLBACK_ANSWER
            return
        if not self.settings.nvidia_api_key:
            yield "NVIDIA API key is not configured. Set NVIDIA_API_KEY and retry."
            return

        prompt = self._build_prompt(question, context_blocks)
        try:
            async with httpx.AsyncClient(timeout=self.settings.nvidia_timeout) as client:
                async with client.stream(
                    "POST",
                    self.generate_url,
                    json=self._payload(prompt, stream=True),
                    headers=self._headers(),
                ) as response:
                    response.raise_for_status()
                    raw = ""
                    emitted = ""
                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        payload = line[5:].strip() if line.startswith("data:") else line.strip()
                        if not payload or payload == "[DONE]":
                            continue
                        data = json.loads(payload)
                        token = (
                            data.get("choices", [{}])[0]
                            .get("delta", {})
                            .get("content")
                        )
                        if token:
                            raw += token
                            cleaned = sanitize_answer(raw)
                            if len(cleaned) > len(emitted):
                                delta = cleaned[len(emitted) :]
                                emitted = cleaned
                                yield delta
                    if not emitted:
                        yield FALLBACK_ANSWER
        except Exception as exc:  # noqa: BLE001
            logger.exception("NVIDIA streaming failed: %s", exc)
            yield (
                "The language model is temporarily unavailable. "
                "Please try again in a moment."
            )


nvidia_client = NvidiaClient()
