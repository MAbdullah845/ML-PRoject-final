from pydantic import BaseModel, Field
from typing import Optional

class APIConfig(BaseModel):
    api_name: str
    api_key: str = Field(default="", exclude=True=True)
    api_url: str
    api_secret: str = Field(default="", exclude=True=True)
    environment: str = "production"

class APIConfigResponse(BaseModel):
    api_name: str
    api_url: str
    environment: str

    class Config:
        from_attributes = True
