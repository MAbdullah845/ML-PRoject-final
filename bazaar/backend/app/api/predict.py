"""Prediction endpoint — 5-bar horizon forecast with walk-forward scores.

Reuses the same data source as /api/market (pypsx when live, mock otherwise)
so predictions stay consistent with what the chart is showing.
"""

from fastapi import APIRouter, HTTPException, Query

from ..core.config import settings
from ..data.ohlcv_service import generate_ohlcv, calculate_indicators
from ..data.market_feed import pypsx_feed, TOOLKIT_AVAILABLE
from ..ml.predictor import train_and_predict
from .market_data import MOCK_SYMBOLS, TF_MAP

router = APIRouter(prefix="/api/predict", tags=["Prediction"])


@router.get("/{symbol}")
async def predict_direction(
    symbol: str,
    timeframe: str = Query("1Y", enum=["3M", "6M", "1Y"], description="More history = better training data"),
):
    """Predict 5-bar up/down using a boosted tree and abstain when weak.

    Reports walk-forward accuracy (every bar) and selective accuracy (only
    bars where model confidence clears an adaptive threshold). Educational,
    not financial advice.
    """
    symbol = symbol.upper()
    source = "mock"
    df = None

    if settings.USE_PYPSX and (pypsx_feed.is_connected or TOOLKIT_AVAILABLE):
        live_df = pypsx_feed.get_ohlcv(symbol, timeframe=timeframe)
        if not live_df.empty and len(live_df) >= 40:
            df = live_df
            source = "pypsx"

    if df is None:
        if symbol not in MOCK_SYMBOLS:
            raise HTTPException(status_code=404, detail=f"Symbol {symbol} not found")
        meta = MOCK_SYMBOLS[symbol]
        count = TF_MAP.get(timeframe, 264)
        df = generate_ohlcv(symbol, meta["base"], meta["vol"], count * 2, meta["baseVol"])
        df = df.tail(count)

    enriched = calculate_indicators(df)
    result = train_and_predict(enriched, symbol)

    return {
        "symbol": result.symbol,
        "timeframe": timeframe,
        "direction": result.direction,
        "signal": result.signal,
        "confidence": result.confidence,
        "prob_up": result.prob_up,
        "prob_down": result.prob_down,
        "holdout_accuracy": result.accuracy,
        "walk_forward_accuracy": result.walk_forward_accuracy,
        "selective_accuracy": result.selective_accuracy,
        "coverage": result.coverage,
        "threshold": result.threshold,
        "horizon_bars": result.horizon_bars,
        "n_walk_forward_folds": result.n_walk_forward_folds,
        "n_training_samples": result.n_samples,
        "last_close": round(result.last_close, 2),
        "features_used": result.features_used,
        "model_available": result.model_available,
        "message": result.message,
        "source": source,
        "disclaimer": "Educational model -- not financial advice. Next-tick prices are not 80% predictable.",
    }
