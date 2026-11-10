from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
import os

router = APIRouter(prefix="/api/config", tags=["Configuration"])

class APIKeyUpdate(BaseModel):
    api_name: str
    api_key: Optional[str] = None
    api_url: Optional[str] = None

_api_configs: dict = {}

@router.get("/")
async def get_config():
    return {
        "configs": {k: {"api_name": k, "api_url": v.get("api_url", "")} for k, v in _api_configs.items()},
        "message": "API credentials should be stored in environment variables, never hardcoded",
    }

@router.post("/")
async def set_config(config: APIKeyUpdate):
    _api_configs[config.api_name] = {
        "api_key": config.api_key or _api_configs.get(config.api_name, {}).get("api_key", ""),
        "api_url": config.api_url or _api_configs.get(config.api_name, {}).get("api_url", ""),
    }
    return {"message": f"Config updated for {config.api_name}"}

@router.get("/env-check")
async def check_env():
    required_keys = ["PSX_API_KEY", "PSX_API_URL", "DATABASE_URL"]
    missing = [k for k in required_keys if not os.environ.get(k)]
    return {
        "has_keys": len(missing) == 0,
        "missing_keys": missing,
        "environment": os.environ.get("ENVIRONMENT", "development"),
    }
