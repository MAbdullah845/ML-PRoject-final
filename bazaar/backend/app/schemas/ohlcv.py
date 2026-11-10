from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class OHLCVBase(BaseModel):
    symbol: str
    timeframe: str
    open: float
    high: float
    low: float
    close: float
    volume: float

class OHLCVCreate(OHLCVBase):
    timestamp: Optional[datetime] = None

class OHLCVResponse(OHLCVBase):
    id: int
    timestamp: datetime

    class Config:
        from_attributes = True

class OHLCVData(BaseModel):
    ohlcv: list[OHLCVResponse]
    symbol: str
    timeframe: str

class OHLCVSlice(BaseModel):
    data: list[dict]
    symbol: str
    timeframe: str
    count: int
