import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Set environment
os.environ['PYPSX_PAPER'] = 'true'
os.environ['PYPSX_API_KEY_ID'] = ''
os.environ['PYPSX_API_SECRET_KEY'] = ''
os.environ['PYPSX_API_TOKEN'] = ''

# Directly test the analysis modules
print("Testing analysis modules directly...\n")

import pandas as pd

# Test 1: ohlcv_service indicators
from backend.app.data.ohlcv_service import calculate_indicators, calculate_ema, calculate_rsi, calculate_macd, calculate_sma, calculate_bollinger_bands, calculate_atr, calculate_volume_indicator

# Create sample OHLCV data
df = pd.DataFrame({
    'timestamp': pd.date_range('2024-01-01', periods=50, freq='1D'),
    'open': [50.0 + i*0.1 for i in range(50)],
    'high': [55.0 + i*0.1 for i in range(50)],
    'low': [45.0 + i*0.1 for i in range(50)],
    'close': [50.0 + i*0.1 for i in range(50)],
    'volume': [1000000] * 50,
})
df = calculate_indicators(df)
print("1. calculate_indicators: OK")
print("   EMA20 sample:", round(float(df['ema_20'].iloc[-1]), 2))
print("   RSI14 sample:", round(float(df['rsi_14'].iloc[-1]), 2))
print("   MACD sample:", round(float(df['macd_hist'].iloc[-1]), 2))
print("   BB sample width:", round(float(df['bb_upper'].iloc[-1]) - float(df['bb_lower'].iloc[-1]), 2))
print("   ATR sample:", round(float(df['atr_14'].iloc[-1]), 2))
print("   Volume MA sample:", round(float(df['volume_ma_20'].iloc[-1]), 0))

# Test 2: Market structure
from backend.app.analysis.market_structure import detect_swings, classify_market_structure
df_swings = detect_swings(df, lookback=5)
structure = classify_market_structure(df_swings)
print("\n2. Market structure: OK")
print("   Trend:", structure.get('trend'))

# Test 3: Support & Resistance
from backend.app.analysis.support_resistance import detect_support_resistance
levels = detect_support_resistance(df_swings, min_touches=2, tolerance_pct=0.02)
print("\n3. Support & Resistance: OK")
print("   Levels detected:", len(levels))
for l in levels[:3]:
    print(f"   - {l['type']}: {l['price']} (touches: {l['touch_count']})")

# Test 4: Pattern recognition
from backend.app.analysis.patterns import PatternRecognizer
patterns = PatternRecognizer.recognize_all_candlestick(df_swings)
print("\n4. Pattern recognition: OK")
print("   Patterns found:", len(patterns))
for p in patterns[:3]:
    ptype = p.get('pattern', p.get('signal', 'unknown'))
    print(f"   - {ptype}")

# Test 5: Divergence
from backend.app.analysis.divergence import DivergenceDetector
rsi_div = DivergenceDetector.detect_rsi_divergence(df_swings)
macd_div = DivergenceDetector.detect_macd_divergence(df_swings)
print("\n5. Divergence: OK")
print("   RSI divergence:", rsi_div.get('divergence') if rsi_div else 'None')
print("   MACD divergence:", macd_div.get('divergence') if macd_div else 'None')

# Test 6: Volatility
from backend.app.analysis.volatility import VolatilityEngine
vol = VolatilityEngine.calculate_volatility_regime(df_swings)
vol_cond = VolatilityEngine.get_volatility_condition(df_swings)
print("\n6. Volatility: OK")
print("   Regime:", vol.get('volatility'))
print("   BB width:", vol.get('bb_width'))
print("   ATR:", vol.get('atr_value'))

# Test 7: Market regime
from backend.app.analysis.market_regime import MarketRegimeEngine
regime = MarketRegimeEngine.determine_regime(
    structure_trend=structure.get('trend', 'Range'),
    volatility=vol.get('volatility', 'Normal'),
    ema20_vs_ema50='neutral',
    atr_pct=vol.get('atr_change_pct', 0.0),
    df=df
)
regime_cond = MarketRegimeEngine.get_regime_condition(regime.get('regime', 'Range'))
print("\n7. Market regime: OK")
print("   Regime:", regime.get('regime'))
print("   Condition:", regime_cond.get('condition'))

# Test 8: Technical conditions
from backend.app.analysis.conditions import TechnicalConditionEngine
conditions = TechnicalConditionEngine.analyze(df, levels, levels, regime)
print("\n8. Technical conditions: OK")
print("   Conditions count:", len(conditions))

# Test 9: Scoring engine
from backend.app.analysis.scoring import ScoringEngine
scoring_engine = ScoringEngine()
aggregated_obj = type('obj', (object,), {
    'bullish_score': 0.6,
    'bearish_score': 0.3,
    'neutral_score': 0.1
})()
scoring_result = scoring_engine.calculate_scores(
    conditions=conditions,
    regime=regime,
    structure=structure,
    support_resistance={'type': 'mixed'},
    indicators={'rsi_bullish': True},
    patterns=patterns,
    volume_condition=vol_cond,
    breakout=None,
    divergence=rsi_div,
    market_regime=regime
)
print("\n9. Scoring engine: OK")
print("   Bullish score:", scoring_result.get('bullish_score'))
print("   Bearish score:", scoring_result.get('bearish_score'))
print("   Neutral score:", scoring_result.get('neutral_score'))
print("   Signal:", scoring_result.get('signal'))

# Test 10: Signal engine
from backend.app.analysis.signal_engine import SignalEngine
signal_engine = SignalEngine()
signal_result = signal_engine.generate_signal(
    scoring_result=scoring_result,
    conditions=conditions,
    regime_condition=regime_cond,
    breakout=None,
    divergence=rsi_div,
    patterns=patterns
)
print("\n10. Signal engine: OK")
print("   Signal:", signal_result.get('signal'))
print("   Confidence:", signal_result.get('confidence'))
print("   Reasons count:", len(signal_result.get('reasons', [])))
print("   Warnings count:", len(signal_result.get('warnings', [])))

# Test 11: Trade levels
from backend.app.analysis.trade_levels import TradeLevelsGenerator
levels_result = TradeLevelsGenerator.calculate_levels(
    signal=signal_result.get('signal', 'WAIT'),
    current_price=100.0,
    support_levels=levels[:3],
    resistance_levels=levels[:3],
    atr_14=float(df['atr_14'].iloc[-1]),
    structure=structure,
    regime=regime,
    risk_reward_ratio=2.0
)
print("\n11. Trade levels: OK")
print("   Entry zone:", levels_result.get('entry_zone'))
print("   Stop loss:", levels_result.get('stop_loss'))
print("   Target 1:", levels_result.get('target_1'))
print("   Target 2:", levels_result.get('target_2'))
print("   Risk:", levels_result.get('risk'))
print("   Reward:", levels_result.get('reward'))
print("   Risk/reward:", levels_result.get('risk_reward'))
print("   Method:", levels_result.get('method'))

print("\n" + "="*50)
print("All direct module tests PASSED!")
print("="*50)