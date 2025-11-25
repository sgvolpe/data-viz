from pathlib import Path

from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache


class Settings(BaseSettings):
    # GENERAL
    APP_NAME: str = "Data Viz App"
    DEBUG: bool = True
    HOST: str = "127.0.0.1"
    FASTAPI_PORT: str = "8000"
    DASH_PORT: str = "8050"

    # DATABASE
    DATABASE_URL: str = Field(default="sqlite:///./app.db")

    # SECURITY
    SECRET_KEY: str = Field(default="CHANGE_ME_TO_A_RANDOM_SECRET")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # DASH
    DASH_ROUTE_PREFIX: str = "/dash/"

    # CORS (optional)
    CORS_ALLOW_ORIGINS: list[str] = ["*"]
    OPEN_AI_KEY: str = Field(default="")
    GROQ_API_KEY: str = Field(default="")

    class Config:
        env_file = Path() / "core" / ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings():
    return Settings()


settings = get_settings()
