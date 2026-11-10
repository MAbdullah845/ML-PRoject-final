import pandas as pd
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ..analysis.market_structure import classify_market_structure, detect_swings
from ..analysis.support_resistance import detect_support_resistance, get_nearest_level
from ..analysis.patterns import PatternRecognizer
from ..analysis.breakout import BreakoutDetector
from ..analysis.divergence import DivergenceDetector
from ..analysis.volatility import VolatilityEngine
from ..analysis.market_regime import MarketRegimeEngine
from ..analysis.conditions import TechnicalConditionEngine, ConditionAggregator
from ..analysis.scoring import ScoringEngine
from ..analysis.signal_engine import SignalEngine
from ..analysis.trade_levels import TradeLevelsGenerator
from ..data.ohlcv_service import calculate_indicators, generate_ohlcv
from ..api.market_data import MOCK_SYMBOLS, TF_MAP
from ..core.config import settings
from ..data.market_feed import pypsx_feed, TOOLKIT_AVAILABLE, PYPSX_AVAILABLE

router = APIRouter(prefix="/api/analysis", tags=["Analysis"])


class AnalysisResponse(BaseModel):
    symbol: str
    timeframe: str
    price: float
    trend: str
    market_structure: Dict[str, Any]
    support: List[Dict[str, Any]]
    resistance: List[Dict[str, Any]]
    patterns: List[Dict[str, Any]]
    indicators: Dict[str, Any]
    volume: Dict[str, Any]
    volatility: Dict[str, Any]
    market_regime: Dict[str, Any]
    conditions: List[Dict[str, Any]]
    bullish_score: float
    bearish_score: float
    neutral_score: float
    signal: str
    confidence: str
    reasons: List[str]
    warnings: List[str]
    trade_levels: Dict[str, Any]
    last_analysis: str


@router.get("/{symbol}")
async def get_analysis(
    symbol: str,
    timeframe: str = Query("3M", enum=["1M", "3M", "6M", "1Y"]),
):
    """Get complete technical analysis for a symbol and timeframe.

    Returns comprehensive analysis including:
    - Market data and indicators
    - Trend, structure, S/R levels
    - Pattern recognition
    - Volume, volatility, market regime
    - Technical conditions and scores
    - Trading signal with reasons
    - Trade levels (entry, targets, stop, R:R)
    """
    symbol = symbol.upper()

    # Validate timeframe
    if timeframe not in ["1M", "3M", "6M", "1Y"]:
        raise HTTPException(status_code=400, detail=f"Invalid timeframe: {timeframe}")

    # Fetch market data
    live = settings.USE_PYPSX and (pypsx_feed.is_connected or TOOLKIT_AVAILABLE)
    source = "pypsx" if live else "mock"

    if live:
        df = pypsx_feed.get_ohlcv(symbol, timeframe=timeframe)
        if df.empty:
            # Fall back to mock if no data
            live = False
            source = "mock"

    if not live or source == "mock":
        if symbol not in MOCK_SYMBOLS:
            raise HTTPException(status_code=404, detail=f"Symbol {symbol} not found")
        meta = MOCK_SYMBOLS[symbol]
        count = TF_MAP.get(timeframe, 66)
        df = generate_ohlcv(symbol, meta["base"], meta["vol"], count * 2, meta["baseVol"])
        df = df.tail(count)

    # Calculate indicators
    df = calculate_indicators(df)

    # Get current price
    last_close = float(df["close"].iloc[-1])

    # --- Market Structure ---
    df_with_swings = detect_swings(df, lookback=5)
    structure = classify_market_structure(df_with_swings)

    # --- Support & Resistance ---
    resistance_levels = detect_support_resistance(df_with_swings, min_touches=2, tolerance_pct=0.02)
    support_levels = detect_support_resistance(df_with_swings, min_touches=2, tolerance_pct=0.02)

    # --- Pattern Recognition ---
    candlestick_patterns = PatternRecognizer.recognize_all_candlestick(df_with_swings)
    chart_patterns = PatternRecognizer.recognize_all_chart(df_with_swings)
    all_patterns = candlestick_patterns + chart_patterns

    # --- Volatility ---
    volatility = VolatilityEngine.calculate_volatility_regime(df)
    vol_condition = VolatilityEngine.get_volatility_condition(df)

    # --- Market Regime ---
    # Build regime from structure and volatility
    ema20 = float(df["ema_20"].iloc[-1]) if "ema_20" in df.columns else None
    ema50 = float(df["ema_50"].iloc[-1]) if "ema_50" in df.columns else None
    last_rsi = float(df["rsi_14"].iloc[-1]) if "rsi_14" in df.columns else None

    ema_alignment = "neutral"
    if ema20 is not None and ema50 is not None:
        ema_alignment = "bullish" if ema20 > ema50 else "bearish"

    regime_input = {
        "structure_trend": structure.get("trend", "Range"),
        "volatility": volatility.get("volatility", "Normal"),
        "ema20_vs_ema50": ema_alignment,
        "atr_pct": volatility.get("atr_change_pct", 0.0),
    }
    regime = MarketRegimeEngine.determine_regime(**regime_input)
    regime_condition = MarketRegimeEngine.get_regime_condition(regime.get("regime", "Range"))

    # --- Technical Conditions ---
    conditions = TechnicalConditionEngine.analyze(df, resistance_levels, support_levels, regime)

    # --- Scoring Engine ---
    scoring_engine = ScoringEngine()
    # Get divergence
    divergence_detector = DivergenceDetector()
    divergence = divergence_detector.detect_rsi_divergence(df) or divergence_detector.detect_macd_divergence(df)

    # Aggregate conditions
    aggregated = ConditionAggregator.aggregate(conditions)

    # --- Signal Engine ---
    signal_engine = SignalEngine()
    signal_result = signal_engine.generate_signal(
        scoring_result=aggregated,
        conditions=conditions,
        regime_condition=regime_condition,
        breakout=None,  # Would be detected separately
        divergence=divergence,
    )

    # --- Trade Levels ---
    atr_14 = float(df["atr_14"].iloc[-1]) if "atr_14" in df.columns else 0
    trade_levels = TradeLevelsGenerator.calculate_levels(
        signal=signal_result.get("signal", "WAIT"),
        current_price=last_close,
        support_levels=support_levels,
        resistance_levels=resistance_levels,
        atr_14=atr_14,
        structure=structure,
        regime=regime,
        risk_reward_ratio=2.0,
    )

    # Build response
    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "price": round(last_close, 2),
        "trend": structure.get("trend", "Range"),
        "market_structure": structure,
        "support": support_levels[:3],  # Top 3 support levels
        "resistance": resistance_levels[:3],  # Top 3 resistance levels
        "patterns": all_patterns[:5],  # Top 5 patterns
        "indicators": {
            "rsi_14": round(last_rsi, 2) if last_rsi is not None else None,
            "ema_20": round(ema20, 2) if ema20 is not None else None,
            "ema_50": round(ema50, 2) if ema50 is not None else None,
            "ema_200": round(float(df["ema_200"].iloc[-1]), 2) if "ema_200" in df.columns else None,
            "macd_hist": round(float(df["macd_hist"].iloc[-1]), 2) if "macd_hist" in df.columns else None,
            "bb_upper": round(float(df["bb_upper"].iloc[-1]), 2) if "bb_upper" in df.columns else None,
            "bb_lower": round(float(df["bb_lower"].iloc[-1]), 2) if "bb_lower" in df.columns else None,
            "atr_14": round(atr_14, 2),
            "volume_ma_20": round(float(df["volume_ma_20"].iloc[-1]), 0) if "volume_ma_20" in df.columns else 0,
            "current_volume": int(float(df["volume"].iloc[-1])) if "volume" in df.columns else 0,
        },
        "volume": vol_condition,
        "volatility": volatility,
        "market_regime": regime,
        "conditions": conditions,
        "bullish_score": aggregated.get("bullish_score", 0.0),
        "bearish_score": aggregated.get("bearish_score", 0.0),
        "neutral_score": aggregated.get("neutral_score", 0.0),
        "signal": signal_result.get("signal", "WAIT"),
        "confidence": signal_result.get("confidence", "Weak"),
        "reasons": signal_result.get("reasons", []),
        "warnings": signal_result.get("warnings", []),
        "trade_levels": trade_levels,
        "last_analysis": pd.Timestamp.now().isoformat(),
    }