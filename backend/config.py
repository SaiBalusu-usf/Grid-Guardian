"""Application configuration loaded from environment variables with sensible defaults."""

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """GridGuardian backend configuration."""

    GOOGLE_CLOUD_PROJECT: str = Field(
        default="grid-guardian-dev",
        description="Google Cloud project ID",
    )
    FIRESTORE_EMULATOR_HOST: str = Field(
        default="",
        description="Firestore emulator host (e.g. localhost:8080). Empty means use real Firestore or in-memory fallback.",
    )
    GEMINI_API_KEY: str = Field(
        default="",
        description="Gemini API key for LLM-backed agents",
    )
    SHELTER_AGENT_URL: str = Field(
        default="http://localhost:8001",
        description="URL of the A2A shelter specialist agent",
    )
    USE_MOCK: str = Field(
        default="true",
        description="When 'true', tools return deterministic mock data instead of calling external services.",
    )
    SSE_ENABLED: str = Field(
        default="true",
        description="Enable server-sent events streaming",
    )
    LOG_LEVEL: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )

    @property
    def is_mock(self) -> bool:
        return self.USE_MOCK.lower() == "true"

    @property
    def is_sse_enabled(self) -> bool:
        return self.SSE_ENABLED.lower() == "true"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


settings = Settings()
