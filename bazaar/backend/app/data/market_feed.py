"""
PyPSX market data + trading integration.

Two separate concerns, two separate SDKs:

  * pypsx-toolkit -> FREE public PSX market data. No account, no API key.
    Used for everything the chart and watchlist need: quotes, OHLCV
    history, market watch, symbol list.

  * pypsx (TradingClient) -> PAID/authenticated account: orders, positions,
    portfolio. Only needed if you actually want to place trades. Market
    data endpoints never depend on this.
"""

import os
import time
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
from dotenv import load_dotenv

_backend_env = Path(__file__).resolve().parent.parent.parent / ".env"
_root_env = _backend_env.parent / ".env"
if _backend_env.exists():
    load_dotenv(_backend_env)
if _root_env.exists():
    load_dotenv(_root_env)
load_dotenv()

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------
# Free market-data SDK (no key required)
# --------------------------------------------------------------------------
try:
    import pypsx_toolkit as toolkit

    TOOLKIT_AVAILABLE = True
except ImportError:
    logger.warning("pypsx-toolkit not installed. Install with: pip install pypsx-toolkit")
    toolkit = None  # type: ignore
    TOOLKIT_AVAILABLE = False

# --------------------------------------------------------------------------
# Paid/authenticated trading SDK (optional — only for placing real orders)
# --------------------------------------------------------------------------
try:
    from pypsx import TradingClient

    PYPSX_AVAILABLE = True
except ImportError:
    logger.warning("pypsx not installed. Install with: pip install pypsx")
    TradingClient = None  # type: ignore
    PYPSX_AVAILABLE = False


class PyPSXFeed:
    """Wrapper around both SDKs with graceful degradation.

    Every method returns an empty DataFrame / dict / list instead of raising,
    so the API layer can always fall back to mock data.
    """

    def __init__(self, paper: Optional[bool] = None):
        self.paper = paper if paper is not None else self._get_paper_mode()
        self.client = None
        self._ohlcv_cache: Dict[str, tuple[float, pd.DataFrame]] = {}
        self._symbols_cache: tuple[float, List[str]] = (0, [])
        self._connect_trading_client()

    # ------------------------------------------------------------------
    # Trading client connection (optional, only needed for orders)
    # ------------------------------------------------------------------
    @staticmethod
    def _get_paper_mode() -> bool:
        val = os.getenv("PYPSX_PAPER")
        if val is not None and val != "":
            return val.strip().lower() in ("true", "1", "yes")
        try:
            from ..core.config import settings
            return bool(settings.PYPSX_PAPER)
        except Exception:
            return True

    def _connect_trading_client(self) -> None:
        if not PYPSX_AVAILABLE:
            return

        api_key_id = os.getenv("PYPSX_API_KEY_ID", "").strip()
        secret_key = os.getenv("PYPSX_API_SECRET_KEY", "").strip()
        api_token = os.getenv("PYPSX_API_TOKEN", "").strip()

        if not (api_key_id and secret_key) and not api_token:
            try:
                from ..core.config import settings
                api_key_id = api_key_id or (settings.PYPSX_API_KEY_ID or "").strip()
                secret_key = secret_key or (settings.PYPSX_API_SECRET_KEY or "").strip()
                api_token = api_token or (settings.PYPSX_API_TOKEN or "").strip()
            except Exception:
                pass

        if not (api_key_id and secret_key) and not api_token:
            # No credentials configured — that's fine, market data still
            # works fully via the free toolkit. Trading endpoints will
            # just report "not connected".
            return

        try:
            if api_token:
                self.client = TradingClient.from_env(paper=self.paper)
            else:
                self.client = TradingClient(
                    api_key=api_key_id,
                    secret_key=secret_key,
                    paper=self.paper,
                    mode="PAPER" if self.paper else "LIVE",
                )
            logger.info("PyPSX TradingClient connected (paper=%s)", self.paper)
        except Exception as exc:
            logger.warning("Trading client not connected (data endpoints are unaffected): %s", exc)
            self.client = None

    @property
    def is_connected(self) -> bool:
        return self.client is not None

    # ------------------------------------------------------------------
    # Market data — PyPSX client first, then free toolkit fallback
    # ------------------------------------------------------------------
    def get_ohlcv(self, symbol: str, timeframe: str = "3M") -> pd.DataFrame:
        """Return a normalised OHLCV DataFrame: timestamp, open, high, low, close, volume."""
        sym = symbol.strip().upper()
        now = time.time()

        days_map = {"1M": 22, "3M": 66, "6M": 132, "1Y": 264}
        count = days_map.get(timeframe.upper(), 66)

        # Check memory cache (60s TTL)
        if sym in self._ohlcv_cache:
            cache_time, cached_df = self._ohlcv_cache[sym]
            if now - cache_time < 60 and not cached_df.empty:
                return cached_df.tail(count)

        # 1. Try authenticated PyPSX TradingClient
        if self.client:
            try:
                bars = self.client.get_historical(sym)
                if bars:
                    df = pd.DataFrame(bars)
                    norm = self._normalise(df)
                    if not norm.empty:
                        self._ohlcv_cache[sym] = (now, norm)
                        return norm.tail(count)
            except Exception as exc:
                logger.warning("PyPSX client get_historical failed for %s: %s", sym, exc)

        # 2. Fallback to free toolkit
        if TOOLKIT_AVAILABLE:
            days = {"1M": 35, "3M": 100, "6M": 200, "1Y": 400}.get(timeframe.upper(), 100)
            try:
                from datetime import date, timedelta
                end = date.today()
                start = end - timedelta(days=days)
                df = toolkit.get_historical(sym, start.isoformat(), end.isoformat())
                if df is not None and not df.empty:
                    norm = self._normalise(df)
                    self._ohlcv_cache[sym] = (now, norm)
                    return norm.tail(count)
            except Exception as exc:
                logger.warning("Free toolkit history failed for %s: %s", sym, exc)

        return pd.DataFrame()

    @staticmethod
    def _normalise(df: pd.DataFrame) -> pd.DataFrame:
        """Lowercase columns and guarantee a timestamp column."""
        df = df.copy()

        # get_historical returns TIME as the index, not a column.
        if df.index.name and str(df.index.name).lower() in ("time", "date", "datetime"):
            df = df.reset_index()

        df.columns = [str(c).strip().lower() for c in df.columns]

        rename = {"date": "timestamp", "datetime": "timestamp", "time": "timestamp", "current": "close"}
        df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})

        if "timestamp" not in df.columns:
            df = df.reset_index()
            df.columns = [str(c).strip().lower() for c in df.columns]
            if "index" in df.columns:
                df = df.rename(columns={"index": "timestamp"})

        keep = [c for c in ["timestamp", "open", "high", "low", "close", "volume"] if c in df.columns]
        return df[keep].dropna(subset=["close"]) if "close" in keep else df[keep]

    def get_market_watch(self) -> pd.DataFrame:
        if not TOOLKIT_AVAILABLE:
            return pd.DataFrame()
        try:
            result = toolkit.get_market_watch()
            return result if isinstance(result, pd.DataFrame) else pd.DataFrame(result)
        except Exception as exc:
            logger.error("Failed to fetch market watch: %s", exc)
            return pd.DataFrame()

    def get_symbols(self) -> List[str]:
        """Tradable symbol universe: tries authenticated PyPSX client, then toolkit."""
        now = time.time()
        if now - self._symbols_cache[0] < 300 and self._symbols_cache[1]:
            return self._symbols_cache[1]

        if self.client:
            try:
                raw = self.client.get_symbols()
                if raw:
                    syms = []
                    for item in raw:
                        if isinstance(item, dict) and "symbol" in item:
                            syms.append(str(item["symbol"]).strip().upper())
                        elif isinstance(item, str):
                            syms.append(item.strip().upper())
                    if syms:
                        res = sorted(set(syms))
                        self._symbols_cache = (now, res)
                        return res
            except Exception as exc:
                logger.warning("PyPSX client get_symbols failed: %s", exc)

        if TOOLKIT_AVAILABLE:
            try:
                syms = toolkit.get_symbols()
                if syms:
                    res = sorted(str(s).upper() for s in syms)
                    self._symbols_cache = (now, res)
                    return res
            except Exception as exc:
                logger.error("Failed to fetch symbols: %s", exc)

        return []

    def get_symbol_info(self, symbol: str) -> Dict[str, Any]:
        sym = symbol.strip().upper()
        if self.client:
            try:
                raw = self.client.get_symbols()
                if raw:
                    for item in raw:
                        if isinstance(item, dict) and str(item.get("symbol", "")).upper() == sym:
                            return {
                                "name": item.get("name") or sym,
                                "company_name": item.get("name") or sym,
                                "sector": item.get("sector"),
                            }
            except Exception:
                pass

        if TOOLKIT_AVAILABLE:
            try:
                return toolkit.PSXTicker(sym).info or {}
            except Exception as exc:
                logger.error("Failed to fetch info for %s: %s", sym, exc)

        return {"name": sym, "company_name": sym}

    def get_quote(self, symbol: str) -> Dict[str, Any]:
        """Price snapshot: last_price, change, change_pct, volume, etc."""
        sym = symbol.strip().upper()

        if self.client:
            try:
                q = self.client.get_quote(sym)
                if q and isinstance(q, dict):
                    last_price = q.get("current") or q.get("price") or q.get("CURRENT")
                    change = q.get("change") or q.get("CHANGE") or 0.0
                    change_pct = q.get("change_pct") or q.get("change_percent") or q.get("%CHANGE") or 0.0
                    volume = q.get("volume") or q.get("VOLUME") or 0
                    return {
                        "last_price": last_price,
                        "change": change,
                        "change_pct": change_pct,
                        "volume": volume,
                        "high": q.get("high") or q.get("HIGH"),
                        "low": q.get("low") or q.get("LOW"),
                        "bid": q.get("bid_price") or q.get("bid") or q.get("BID"),
                        "ask": q.get("ask_price") or q.get("ask") or q.get("ASK"),
                        "pe_ratio": q.get("pe") or q.get("PE"),
                        "week_52_range": q.get("52w_range") or q.get("52W RANGE"),
                    }
            except Exception as exc:
                logger.warning("PyPSX client get_quote failed for %s: %s", sym, exc)

        if TOOLKIT_AVAILABLE:
            try:
                q = toolkit.get_quote(sym, format="json")
                if not q:
                    return {}
                return {
                    "last_price": q.get("CURRENT") or q.get("current"),
                    "change": q.get("CHANGE") or q.get("change"),
                    "change_pct": q.get("%CHANGE") or q.get("change_pct"),
                    "volume": q.get("VOLUME") or q.get("volume"),
                    "bid": q.get("BID") or q.get("bid"),
                    "ask": q.get("ASK") or q.get("ask"),
                    "pe_ratio": q.get("PE") or q.get("pe"),
                    "week_52_range": q.get("52W RANGE") or q.get("52w_range"),
                }
            except Exception as exc:
                logger.error("Failed to fetch quote for %s: %s", sym, exc)

        return {}

    # ------------------------------------------------------------------
    # Account & portfolio (requires the paid TradingClient)
    # ------------------------------------------------------------------
    def get_account(self) -> Dict[str, Any]:
        if not self.client:
            return {}
        try:
            return self.client.get_account()
        except Exception as exc:
            logger.error("Failed to fetch account: %s", exc)
            return {}

    def get_portfolio(self) -> Dict[str, Any]:
        if not self.client:
            return {}
        try:
            return self.client.get_portfolio_valuation()
        except Exception as exc:
            logger.error("Failed to fetch portfolio valuation: %s", exc)
            return {}

    def get_positions(self) -> List[Dict[str, Any]]:
        if not self.client:
            return []
        try:
            return self.client.get_positions()
        except Exception as exc:
            logger.error("Failed to fetch positions: %s", exc)
            return []

    # ------------------------------------------------------------------
    # Orders (requires the paid TradingClient)
    # ------------------------------------------------------------------
    def submit_order(
        self,
        symbol: str,
        side: str,
        qty: int,
        order_type: str = "market",
        limit_price: Optional[float] = None,
        stop_price: Optional[float] = None,
    ) -> Dict[str, Any]:
        if not self.client:
            return {"status": "error", "message": "Trading client not connected (market data still works without it)"}

        try:
            order = self.client.place_order(
                symbol=symbol.upper(),
                side=side.upper(),
                quantity=int(qty),
                order_type=order_type.upper(),
                limit_price=limit_price,
                stop_price=stop_price,
            )
            logger.info("Order submitted: %s", order)
            return order
        except Exception as exc:
            logger.error("Failed to submit order: %s", exc)
            return {"status": "error", "message": str(exc)}

    def get_orders(self) -> List[Dict[str, Any]]:
        if not self.client:
            return []
        try:
            return self.client.get_orders()
        except Exception as exc:
            logger.error("Failed to fetch orders: %s", exc)
            return []

    def cancel_order(self, order_id: str) -> Dict[str, Any]:
        if not self.client:
            return {"status": "error", "message": "Trading client not connected"}
        try:
            return self.client.cancel_order(order_id)
        except Exception as exc:
            logger.error("Failed to cancel order %s: %s", order_id, exc)
            return {"status": "error", "message": str(exc)}

    def close(self) -> None:
        closer = getattr(self.client, "close", None)
        if callable(closer):
            try:
                closer()
                logger.info("PyPSX client closed")
            except Exception as exc:
                logger.warning("Error closing PyPSX client: %s", exc)


pypsx_feed = PyPSXFeed()
