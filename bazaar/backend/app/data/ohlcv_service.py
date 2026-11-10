import pandas as pd
import numpy as np
from typing import Optional
from datetime import datetime, timedelta

def generate_ohlcv(
    symbol: str,
    base_price: float,
    volatility: float,
    n_bars: int,
    base_volume: int,
    seed: int = 42,
) -> pd.DataFrame:
    np.random.seed(seed)
    rng = np.random.default_rng(seed)

    timestamps = pd.date_range(
        start=datetime.utcnow() - timedelta(days=n_bars // 24),
        periods=n_bars,
        freq="1H",
    )

    opens = []
    highs = []
    lows = []
    closes = []
    volumes = []

    price = base_price
    for _ in range(n_bars):
        drift = (rng.random() - 0.48) * volatility
        open_price = price
        close_price = max(0.5, open_price * (1 + drift))
        high_price = max(open_price, close_price) * (1 + rng.random() * volatility * 0.55)
        low_price = min(open_price, close_price) * (1 - rng.random() * volatility * 0.55)
        volume = int((rng.random() * 0.6 + 0.45) * base_volume)

        opens.append(open_price)
        highs.append(high_price)
        lows.append(low_price)
        closes.append(close_price)
        volumes.append(volume)
        price = close_price

    return pd.DataFrame({
        "timestamp": timestamps,
        "symbol": symbol,
        "timeframe": "1H",
        "open": opens,
        "high": highs,
        "low": lows,
        "close": closes,
        "volume": volumes,
    })

def slice_ohlcv(df: pd.DataFrame, timeframe: str, n: int) -> pd.DataFrame:
    tf_map = {"1M": 22, "3M": 66, "6M": 132, "1Y": 264}
    count = tf_map.get(timeframe, 66)
    return df.tail(count)

def calculate_sma(series: pd.Series, period: int) -> pd.Series:
    return series.rolling(window=period).mean()

def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.ewm(alpha=1 / period, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def calculate_macd(series: pd.Series, fast=12, slow=26, signal=9) -> pd.Series:
    ema_fast = series.ewm(span=fast).mean()
    ema_slow = series.ewm(span=slow).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal).mean()
    return macd_line - signal_line

def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df['sma_20'] = calculate_sma(df['close'], 20)
    df['rsi_14'] = calculate_rsi(df['close'], 14)
    df['macd_hist'] = calculate_macd(df['close'])
    df['sma_50'] = calculate_sma(df['close'], 50)
    return df
