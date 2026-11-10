from sqlalchemy import Column, Integer, Float, String, DateTime, Index
from sqlalchemy.ext.asyncio import declarative_base
from datetime import datetime

Base = declarative_base()

class OHLCV(Base):
    __tablename__ = "ohlcv_data"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    symbol = Column(String(10), nullable=False, index=True)
    timeframe = Column(String(10), nullable=False, index=True)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)

    __table_args__ = (
        Index("ix_ohlcv_symbol_timeframe", "symbol", "timeframe"),
        Index("ix_ohlcv_timestamp", "timestamp"),
    )

    def to_dict(self):
        return {
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
        }
