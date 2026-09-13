from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List, Optional
import json


class Settings(BaseSettings):
    DATABASE_URL: str
    LLM_PROVIDER: str = "openai"
    OPENAI_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    DEBUG: bool = False
    MAX_UPLOAD_SIZE_MB: int = 10
    # Kept as a plain string (not List[str]) on purpose: pydantic-settings
    # tries to JSON-decode any env var bound to a list-typed field *before*
    # field validators run, so a plain value like
    # "https://app.onrender.com" (valid, easy to paste in Render's UI) would
    # blow up at the settings-source level with a SettingsError, never
    # reaching our own parsing logic below. See `allowed_origins_list`.
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    @property
    def allowed_origins_list(self) -> List[str]:
        # Accept either a JSON list (`["https://a.com","https://b.com"]`) or a
        # plain comma-separated string (`https://a.com,https://b.com`).
        v = self.ALLOWED_ORIGINS.strip()
        if v.startswith("["):
            return json.loads(v)
        return [origin.strip() for origin in v.split(",") if origin.strip()]

    @field_validator("SECRET_KEY")
    @classmethod
    def secret_key_must_be_strong(cls, v):
        if not v or v == "your_generated_secret_key_here" or len(v) < 32:
            raise ValueError(
                "SECRET_KEY must be set to a random string of at least 32 characters. "
                "Generate one with: python -c \"import secrets; print(secrets.token_urlsafe(48))\""
            )
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
