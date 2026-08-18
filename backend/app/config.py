from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "University Knowledge AI"
    environment: str = "development"
    secret_key: str = "change-me-to-a-long-random-secret-key-in-production"
    access_token_expire_minutes: int = 1440
    algorithm: str = "HS256"

    database_url: str = (
        "postgresql+asyncpg://uni_ai:uni_ai_secret@localhost:5432/university_ai"
    )

    cors_origins: str = "http://localhost:3000"

    nvidia_api_key: str = ""
    nvidia_base_url: str = "https://integrate.api.nvidia.com/v1"
    nvidia_model: str = "meta/llama-3.1-8b-instruct"
    nvidia_timeout: int = 120

    embedding_model: str = "BAAI/bge-m3"
    embedding_dimension: int = 1024
    embedding_device: str = "cpu"

    chunk_size: int = 800
    chunk_overlap: int = 150
    top_k: int = 5
    similarity_threshold: float = 0.35

    upload_dir: str = "./uploads"
    max_upload_size_mb: int = 25

    admin_email: str = "admin@university.edu"
    admin_password: str = "Admin123!"
    student_email: str = "student@university.edu"
    student_password: str = "Student123!"

    @property
    def cors_origin_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()
