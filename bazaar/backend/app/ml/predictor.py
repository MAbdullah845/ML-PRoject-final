"""
Horizon-ahead direction predictor.

Predicts whether a 5-bar trade would finish up, not the next tick. Next-bar
direction on liquid stocks is close to a coin flip; a short triple-barrier
label plus abstaining on weak probabilities is the realistic way to raise
*usable* accuracy.

Walk-forward TimeSeriesSplit is used for the reported score. The live call
refits on all labeled rows. This is still a student model, not financial advice.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.model_selection import TimeSeriesSplit, train_test_split

logger = logging.getLogger(__name__)

HORIZON_BARS = 5
ATR_MULT = 1.5
MIN_ROWS_REQUIRED = 60
SELECTIVE_MIN_COVERAGE = 0.20

FEATURE_COLUMNS = [
    "return_1d",
    "return_5d",
    "return_10d",
    "sma20_gap",
    "sma50_gap",
    "rsi_14",
    "macd_hist",
    "volume_change",
    "volume_z",
    "atr_pct",
    "bb_pct",
    "dist_high_20",
    "dist_low_20",
    "intraday_range",
    "trend_sma",
]


@dataclass
class PredictionResult:
    symbol: str
    direction: str  # "up", "down", or "unknown"
    confidence: float
    prob_up: float
    prob_down: float
    accuracy: Optional[float]
    n_samples: int
    last_close: float
    features_used: dict
    model_available: bool
    message: Optional[str] = None
    signal: str = "WAIT"  # BUY, SELL, WAIT
    horizon_bars: int = HORIZON_BARS
    walk_forward_accuracy: Optional[float] = None
    selective_accuracy: Optional[float] = None
    coverage: Optional[float] = None
    threshold: float = 0.55
    n_walk_forward_folds: int = 0
    extras: dict = field(default_factory=dict)


def _safe_div(num: pd.Series, den: pd.Series) -> pd.Series:
    den = den.replace(0, np.nan)
    return num / den


def build_features(df: pd.DataFrame, horizon: int = HORIZON_BARS) -> pd.DataFrame:
    """Engineer features and a 5-bar triple-barrier-style target.

    Target 1 = upside barrier (1.5 ATR) is hit first, or close is higher at
    horizon if neither barrier is hit. Target 0 = downside barrier first /
    lower close. Last `horizon` rows have no label.
    """
    d = df.copy().reset_index(drop=True)
    close = d["close"]
    high = d["high"] if "high" in d.columns else close
    low = d["low"] if "low" in d.columns else close
    volume = d["volume"] if "volume" in d.columns else pd.Series(1.0, index=d.index)

    d["return_1d"] = close.pct_change()
    d["return_5d"] = close.pct_change(5)
    d["return_10d"] = close.pct_change(10)

    sma20 = d["sma_20"] if "sma_20" in d.columns else close.rolling(20).mean()
    sma50 = d["sma_50"] if "sma_50" in d.columns else close.rolling(50).mean()
    d["sma20_gap"] = _safe_div(close - sma20, sma20)
    d["sma50_gap"] = _safe_div(close - sma50, sma50)
    d["trend_sma"] = (close > sma20).astype(float)

    if "rsi_14" not in d.columns:
        d["rsi_14"] = np.nan
    if "macd_hist" not in d.columns:
        d["macd_hist"] = 0.0

    d["volume_change"] = volume.pct_change()
    vol_ma = volume.rolling(20).mean()
    vol_sd = volume.rolling(20).std()
    d["volume_z"] = _safe_div(volume - vol_ma, vol_sd)

    atr = d["atr_14"] if "atr_14" in d.columns else (high - low).rolling(14).mean()
    d["atr_pct"] = _safe_div(atr, close)

    if "bb_upper" in d.columns and "bb_lower" in d.columns:
        span = d["bb_upper"] - d["bb_lower"]
        d["bb_pct"] = _safe_div(close - d["bb_lower"], span)
    else:
        d["bb_pct"] = 0.5

    roll_high = high.rolling(20).max()
    roll_low = low.rolling(20).min()
    d["dist_high_20"] = _safe_div(close, roll_high) - 1.0
    d["dist_low_20"] = _safe_div(close, roll_low) - 1.0
    d["intraday_range"] = _safe_div(high - low, close)

    d["target"] = _triple_barrier_labels(close, high, low, atr, horizon, ATR_MULT)
    return d.replace([np.inf, -np.inf], np.nan)


def _triple_barrier_labels(
    close: pd.Series,
    high: pd.Series,
    low: pd.Series,
    atr: pd.Series,
    horizon: int,
    atr_mult: float,
) -> pd.Series:
    n = len(close)
    labels = np.full(n, np.nan)
    c = close.to_numpy(dtype=float)
    h = high.to_numpy(dtype=float)
    l = low.to_numpy(dtype=float)
    a = atr.to_numpy(dtype=float)

    for i in range(n - horizon):
        width = a[i]
        if not np.isfinite(width) or width <= 0:
            labels[i] = 1.0 if c[i + horizon] > c[i] else 0.0
            continue
        up = c[i] + atr_mult * width
        down = c[i] - atr_mult * width
        hit = None
        for j in range(1, horizon + 1):
            if h[i + j] >= up:
                hit = 1.0
                break
            if l[i + j] <= down:
                hit = 0.0
                break
        if hit is None:
            hit = 1.0 if c[i + horizon] > c[i] else 0.0
        labels[i] = hit
    return pd.Series(labels, index=close.index)


def _make_model():
    try:
        return HistGradientBoostingClassifier(
            max_depth=3,
            learning_rate=0.06,
            max_iter=120,
            l2_regularization=0.15,
            min_samples_leaf=10,
            random_state=42,
        )
    except TypeError:
        return RandomForestClassifier(
            n_estimators=200,
            max_depth=4,
            min_samples_leaf=4,
            random_state=42,
            class_weight="balanced",
        )


def _class_proba(model, X: pd.DataFrame) -> np.ndarray:
    """Return (n, 2) array of [p_down, p_up]."""
    proba = model.predict_proba(X)
    classes = list(model.classes_)
    n = len(X)
    out = np.full((n, 2), 0.5)
    if 0 in classes:
        out[:, 0] = proba[:, classes.index(0)]
    if 1 in classes:
        out[:, 1] = proba[:, classes.index(1)]
    return out


def _walk_forward_scores(X: pd.DataFrame, y: pd.Series) -> dict:
    n = len(X)
    n_splits = min(5, max(2, n // 40))
    if n < 40:
        test_size = max(8, int(n * 0.2))
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, shuffle=False
        )
        model = _make_model()
        model.fit(X_train, y_train)
        proba = _class_proba(model, X_test)
        return _score_probas(y_test.to_numpy(), proba, n_folds=1)

    tscv = TimeSeriesSplit(n_splits=n_splits)
    y_true = []
    probas = []
    for train_idx, test_idx in tscv.split(X):
        if len(train_idx) < 25 or y.iloc[train_idx].nunique() < 2:
            continue
        model = _make_model()
        model.fit(X.iloc[train_idx], y.iloc[train_idx])
        probas.append(_class_proba(model, X.iloc[test_idx]))
        y_true.append(y.iloc[test_idx].to_numpy())

    if not y_true:
        return {"accuracy": None, "selective_accuracy": None, "coverage": None, "threshold": 0.55, "n_folds": 0}

    y_cat = np.concatenate(y_true)
    p_cat = np.vstack(probas)
    return _score_probas(y_cat, p_cat, n_folds=len(y_true))


def _score_probas(y_true: np.ndarray, proba: np.ndarray, n_folds: int) -> dict:
    pred = (proba[:, 1] >= proba[:, 0]).astype(int)
    accuracy = float(accuracy_score(y_true, pred)) if len(y_true) else None

    best_t, best_acc, best_cov = 0.55, accuracy, 1.0
    for t in np.round(np.arange(0.52, 0.72, 0.02), 2):
        conf = np.maximum(proba[:, 1], proba[:, 0])
        mask = conf >= t
        cov = float(mask.mean()) if len(mask) else 0.0
        if mask.sum() < 8 or cov < SELECTIVE_MIN_COVERAGE:
            continue
        acc = float(accuracy_score(y_true[mask], pred[mask]))
        # Prefer higher accuracy; require coverage floor already applied.
        if acc > (best_acc or 0) + 1e-9:
            best_t, best_acc, best_cov = float(t), acc, cov

    return {
        "accuracy": accuracy,
        "selective_accuracy": best_acc,
        "coverage": best_cov,
        "threshold": best_t,
        "n_folds": n_folds,
    }


def train_and_predict(df: pd.DataFrame, symbol: str) -> PredictionResult:
    """Train a fresh model on df and predict the next horizon's direction."""
    d = build_features(df)
    last_close = float(d["close"].iloc[-1]) if len(d) else 0.0

    feature_rows = d.dropna(subset=FEATURE_COLUMNS)
    labeled_rows = feature_rows.dropna(subset=["target"])

    empty = PredictionResult(
        symbol=symbol,
        direction="unknown",
        confidence=0.0,
        prob_up=0.5,
        prob_down=0.5,
        accuracy=None,
        n_samples=len(labeled_rows),
        last_close=last_close,
        features_used={},
        model_available=False,
        signal="WAIT",
    )

    if len(labeled_rows) < MIN_ROWS_REQUIRED:
        empty.message = (
            f"Not enough history to train (have {len(labeled_rows)}, need {MIN_ROWS_REQUIRED}+). "
            "Use the 1Y timeframe."
        )
        return empty

    X = labeled_rows[FEATURE_COLUMNS]
    y = labeled_rows["target"].astype(int)
    if y.nunique() < 2:
        empty.n_samples = len(labeled_rows)
        empty.message = "Not enough class variety in labels to train."
        return empty

    scores = _walk_forward_scores(X, y)
    threshold = scores["threshold"] or 0.55

    model = _make_model()
    model.fit(X, y)

    latest_features = feature_rows[FEATURE_COLUMNS].iloc[[-1]]
    proba = _class_proba(model, latest_features)[0]
    prob_down, prob_up = float(proba[0]), float(proba[1])
    direction = "up" if prob_up >= prob_down else "down"
    confidence = max(prob_up, prob_down)

    if confidence >= threshold and direction == "up":
        signal = "BUY"
    elif confidence >= threshold and direction == "down":
        signal = "SELL"
    else:
        signal = "WAIT"

    wf = scores["accuracy"]
    sel = scores["selective_accuracy"]
    cov = scores["coverage"]

    message = (
        f"{HORIZON_BARS}-bar horizon. Walk-forward {wf:.0%} unfiltered"
        if wf is not None
        else f"{HORIZON_BARS}-bar horizon."
    )
    if sel is not None and cov is not None:
        message += f"; {sel:.0%} when confidence >= {threshold:.0%} (acts on {cov:.0%} of bars)."
    if signal == "WAIT":
        message += " Current setup is too close to a coin flip -- no trade."

    return PredictionResult(
        symbol=symbol,
        direction=direction,
        confidence=round(confidence, 4),
        prob_up=round(prob_up, 4),
        prob_down=round(prob_down, 4),
        accuracy=round(wf, 4) if wf is not None else None,
        n_samples=len(labeled_rows),
        last_close=last_close,
        features_used={c: round(float(latest_features[c].iloc[0]), 4) for c in FEATURE_COLUMNS},
        model_available=True,
        message=message,
        signal=signal,
        horizon_bars=HORIZON_BARS,
        walk_forward_accuracy=round(wf, 4) if wf is not None else None,
        selective_accuracy=round(sel, 4) if sel is not None else None,
        coverage=round(cov, 4) if cov is not None else None,
        threshold=round(threshold, 4),
        n_walk_forward_folds=int(scores["n_folds"] or 0),
    )
