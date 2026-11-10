from pathlib import Path
from pydantic import ConfigDict
from pydantic_settings import BaseSettings
from functools import lru_cache

_backend_dir = Path(__file__).resolve().parent.parent.parent
_root_dir = _backend_dir.parent

class Settings(BaseSettings):
    APP_NAME: str = "Bazaar PSX Terminal"
    APP_VERSION: str = "1.0.0"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/bazaar"
    DATABASE_URL_ASYNC: str = "postgresql+asyncpg://postgres:password@localhost:5432/bazaar"
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    RATE_LIMIT_PER_MINUTE: int = 60
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    PSX_API_KEY: str = ""
    PSX_API_URL: str = ""
    PSX_API_SECRET: str = ""
    REDIS_URL: str = "redis://localhost:6379"
    PYPSX_API_KEY_ID: str = ""
    PYPSX_API_SECRET_KEY: str = ""
    PYPSX_API_TOKEN: str = ""
    PYPSX_PAPER: bool = True
    USE_PYPSX: bool = True
    ALLOW_LIVE_TRADING: bool = False

    model_config = ConfigDict(
        env_file=(
            str(_backend_dir / ".env"),
            str(_root_dir / ".env"),
            ".env",
        ),
        extra="ignore",
    )

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
