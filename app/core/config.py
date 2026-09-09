import os
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "ArenaPulse API"
    environment: str = "development"
    database_url: str = (
        "sqlite:////tmp/arenapulse.db" if os.getenv("VERCEL") else "sqlite:///./arenapulse.db"
    )
    jwt_secret: str = "development-only-change-me"
    access_token_expire_minutes: int = 60
    cors_origins: str = (
        "http://localhost:3000,http://localhost:4173,http://localhost:5173,"
        "http://127.0.0.1:4173"
    )

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
