import pandas as pd
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..core.config import settings
from ..data.ohlcv_service import generate_ohlcv, calculate_indicators
from ..data.market_feed import pypsx_feed, PYPSX_AVAILABLE, TOOLKIT_AVAILABLE

router = APIRouter(prefix="/api/market", tags=["Market Data"])

MOCK_SYMBOLS = {
    "OGDC": {"base": 98.4, "vol": 0.026, "baseVol": 8200000},
    "LUCK": {"base": 781, "vol": 0.021, "baseVol": 900000},
    "ENGRO": {"base": 311, "vol": 0.019, "baseVol": 1150000},
    "HBL": {"base": 118, "vol": 0.020, "baseVol": 3050000},
    "PSO": {"base": 212, "vol": 0.031, "baseVol": 2450000},
    "MEBL": {"base": 166, "vol": 0.021, "baseVol": 1980000},
    "FFC": {"base": 135, "vol": 0.017, "baseVol": 1750000},
    "PPL": {"base": 112, "vol": 0.025, "baseVol": 3950000},
}

TF_MAP = {"1M": 22, "3M": 66, "6M": 132, "1Y": 264}


def live_enabled() -> bool:
    """Live data is used when USE_PYPSX=True and either PyPSX client is connected or toolkit is available."""
    return settings.USE_PYPSX and (pypsx_feed.is_connected or TOOLKIT_AVAILABLE)


@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "bazaar-psx-backend",
        "pypsx_sdk": PYPSX_AVAILABLE,
        "pypsx_toolkit": TOOLKIT_AVAILABLE,
        "live_data": live_enabled(),
        "trading_client": pypsx_feed.is_connected,
        "paper_mode": pypsx_feed.paper,
    }


@router.get("/symbols")
async def get_symbols():
    if settings.USE_PYPSX:
        syms = pypsx_feed.get_symbols()
        if syms:
            return {"symbols": syms, "source": "pypsx"}

        df = pypsx_feed.get_market_watch()
        if not df.empty:
            col = "Symbol" if "Symbol" in df.columns else df.columns[0]
            return {"symbols": sorted(df[col].astype(str).unique().tolist()), "source": "pypsx"}

    return {"symbols": list(MOCK_SYMBOLS.keys()), "source": "mock"}


@router.get("/market-watch")
async def get_market_watch(limit: int = Query(100, ge=1, le=600)):
    """Full PSX market watch — every listed security with its current price."""
    if live_enabled():
        df = pypsx_feed.get_market_watch()
        if not df.empty:
            return {"data": df.head(limit).to_dict(orient="records"), "count": min(limit, len(df)), "source": "pypsx"}

    rows = []
    for sym, meta in MOCK_SYMBOLS.items():
        df = generate_ohlcv(sym, meta["base"], meta["vol"], 60, meta["baseVol"])
        last, prev = float(df["close"].iloc[-1]), float(df["close"].iloc[-2])
        rows.append({
            "Symbol": sym,
            "Current": round(last, 2),
            "Change": round(last - prev, 2),
            "Change%": round((last - prev) / prev * 100, 2),
            "Volume": int(df["volume"].iloc[-1]),
        })
    return {"data": rows, "count": len(rows), "source": "mock"}


@router.get("/quote/{symbol}")
async def get_quote(symbol: str):
    """Fast price snapshot for a single symbol."""
    symbol = symbol.upper()
    if settings.USE_PYPSX:
        quote = pypsx_feed.get_quote(symbol)
        if quote:
            return {"symbol": symbol, "quote": quote, "source": "pypsx"}

    if symbol not in MOCK_SYMBOLS:
        raise HTTPException(status_code=404, detail=f"Symbol {symbol} not found")
    meta = MOCK_SYMBOLS[symbol]
    df = generate_ohlcv(symbol, meta["base"], meta["vol"], 60, meta["baseVol"])
    last, prev = float(df["close"].iloc[-1]), float(df["close"].iloc[-2])
    return {
        "symbol": symbol,
        "quote": {
            "last_price": round(last, 2),
            "change": round(last - prev, 2),
            "change_pct": round((last - prev) / prev * 100, 2),
            "volume": int(df["volume"].iloc[-1]),
        },
        "source": "mock",
    }


@router.get("/ohlcv/{symbol}")
async def get_ohlcv(
    symbol: str,
    timeframe: str = Query("3M", enum=["1M", "3M", "6M", "1Y"]),
    limit: Optional[int] = Query(None, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    symbol = symbol.upper()

    if live_enabled():
        df = pypsx_feed.get_ohlcv(symbol, timeframe=timeframe)
        if not df.empty:
            if limit:
                df = df.tail(limit)
            df = calculate_indicators(df)
            return {
                "data": _records(df, symbol, timeframe),
                "symbol": symbol,
                "timeframe": timeframe,
                "count": len(df),
                "source": "pypsx",
            }

    if symbol not in MOCK_SYMBOLS:
        raise HTTPException(status_code=404, detail=f"Symbol {symbol} not found")

    meta = MOCK_SYMBOLS[symbol]
    count = TF_MAP.get(timeframe, 66)
    if limit:
        count = min(count, limit)

    df = generate_ohlcv(symbol, meta["base"], meta["vol"], count * 2, meta["baseVol"])
    indicators = calculate_indicators(df.tail(count))

    return {
        "data": _records(indicators, symbol, timeframe),
        "symbol": symbol,
        "timeframe": timeframe,
        "count": count,
        "source": "mock",
    }


def _records(df: pd.DataFrame, symbol: str, timeframe: str) -> list[dict]:
    """Serialise an indicator-enriched DataFrame into JSON-safe records."""
    def num(row, key):
        val = row.get(key)
        return float(val) if val is not None and pd.notna(val) else None

    out = []
    for _, row in df.iterrows():
        ts = row.get("timestamp")
        out.append({
            "timestamp": ts.isoformat() if hasattr(ts, "isoformat") else str(ts),
            "symbol": symbol,
            "timeframe": timeframe,
            "open": num(row, "open"),
            "high": num(row, "high"),
            "low": num(row, "low"),
            "close": num(row, "close"),
            "volume": num(row, "volume"),
            "sma_20": num(row, "sma_20"),
            "sma_50": num(row, "sma_50"),
            "rsi_14": num(row, "rsi_14"),
            "macd_hist": num(row, "macd_hist"),
        })
    return out


@router.get("/ohlcv/{symbol}/summary")
async def get_summary(symbol: str, timeframe: str = Query("3M", enum=["1M", "3M", "6M", "1Y"])):
    symbol = symbol.upper()
    source = "mock"
    df = pd.DataFrame()
    name = symbol

    if live_enabled():
        df = pypsx_feed.get_ohlcv(symbol, timeframe=timeframe)
        if not df.empty:
            source = "pypsx"
            info = pypsx_feed.get_symbol_info(symbol)
            name = info.get("company_name") or info.get("name") or symbol

    if df.empty:
        if symbol not in MOCK_SYMBOLS:
            raise HTTPException(status_code=404, detail=f"Symbol {symbol} not found")
        meta = MOCK_SYMBOLS[symbol]
        df = generate_ohlcv(symbol, meta["base"], meta["vol"], TF_MAP.get(timeframe, 66) * 2, meta["baseVol"])
        df = df.tail(TF_MAP.get(timeframe, 66))

    enriched = calculate_indicators(df)
    last_close = float(enriched["close"].iloc[-1])
    prev_close = float(enriched["close"].iloc[-2]) if len(enriched) > 1 else last_close
    sma_20 = enriched["sma_20"].iloc[-1]
    rsi_14 = enriched["rsi_14"].iloc[-1]
    has_sma = pd.notna(sma_20)

    return {
        "symbol": symbol,
        "name": name,
        "last_price": round(last_close, 2),
        "pct_change": round((last_close - prev_close) / prev_close * 100, 2) if prev_close else 0.0,
        "sma_20": round(float(sma_20), 2) if has_sma else None,
        "vs_sma20": round((last_close - float(sma_20)) / float(sma_20) * 100, 2) if has_sma else None,
        "rsi_14": round(float(rsi_14), 2) if pd.notna(rsi_14) else None,
        "resistance_60d": round(float(enriched["high"].tail(60).max()), 2),
        "support_60d": round(float(enriched["low"].tail(60).min()), 2),
        "trend": "Uptrend" if has_sma and last_close >= float(sma_20) else "Downtrend",
        "source": source,
    }
