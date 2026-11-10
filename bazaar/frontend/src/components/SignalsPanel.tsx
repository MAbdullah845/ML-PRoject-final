import { useEffect, useMemo } from 'react';
import { useStore } from '../store/useStore';
import { DEFAULT_SYMBOLS } from '../data/symbols';
import { fmt, sma, rsi, macdHist } from '../utils/indicators';
import { useMarketDataContext } from '../context/MarketDataContext';

/* ------------------------------------------------------------------ */
/*  Helpers                                                           */
/* ------------------------------------------------------------------ */

/** Map confidence + direction into a human-readable strength label */
function strengthLabel(pred: any): { label: string; cls: string } {
  if (!pred || !pred.model_available) return { label: 'N/A', cls: 'neutral' };
  const conf = pred.confidence;
  const up = pred.direction === 'up';

  if (conf >= 0.80) return { label: up ? 'STRONG BUY'  : 'STRONG SELL', cls: up ? 'strong-up' : 'strong-down' };
  if (conf >= 0.60) return { label: up ? 'BUY'         : 'SELL',        cls: up ? 'up'        : 'down' };
  return              { label: 'HOLD',                                  cls: 'neutral' };
}

/** Build 3-5 bullet-point justification reasons from technicals + prediction */
function buildReasons(pred: any, closes: number[]): string[] {
  const reasons: string[] = [];
  if (!closes.length || !pred?.model_available) return ['Insufficient data for analysis.'];

  const n = closes.length;
  const lastClose = closes[n - 1];

  // 1. Trend vs SMA-20
  const sma20 = sma(closes, 20);
  const lastSma = sma20[sma20.length - 1];
  if (lastSma != null) {
    const gap = ((lastClose - lastSma) / lastSma) * 100;
    if (gap > 1)       reasons.push(`Price is ${fmt(gap, 1)}% above the 20-day SMA — bullish trend.`);
    else if (gap < -1) reasons.push(`Price is ${fmt(Math.abs(gap), 1)}% below the 20-day SMA — bearish trend.`);
    else               reasons.push(`Price is near the 20-day SMA — trend is neutral.`);
  }

  // 2. RSI
  const rsiArr = rsi(closes, 14);
  const lastRsi = rsiArr[n - 1];
  if (lastRsi != null) {
    if (lastRsi >= 70)      reasons.push(`RSI at ${fmt(lastRsi, 0)} — overbought territory, reversal risk.`);
    else if (lastRsi <= 30) reasons.push(`RSI at ${fmt(lastRsi, 0)} — oversold territory, bounce potential.`);
    else                    reasons.push(`RSI at ${fmt(lastRsi, 0)} — momentum in neutral zone.`);
  }

  // 3. MACD
  const hist = macdHist(closes);
  const lastHist = hist[n - 1];
  const prevHist = hist[n - 2];
  if (lastHist != null && prevHist != null) {
    if (lastHist > 0 && prevHist <= 0)      reasons.push('MACD histogram crossed above zero — bullish crossover.');
    else if (lastHist < 0 && prevHist >= 0)  reasons.push('MACD histogram crossed below zero — bearish crossover.');
    else if (lastHist > 0)                   reasons.push('MACD histogram positive — bullish momentum continues.');
    else                                     reasons.push('MACD histogram negative — bearish momentum persists.');
  }

  // 4. Volume trend (last 5 vs previous 20)
  if (n > 25) {
    // volume not available in closes, skip — we only have close prices here
  }

  // 5. Support / Resistance proximity
  const window = closes.slice(-Math.min(60, n));
  const support = Math.min(...window);
  const resistance = Math.max(...window);
  const range = resistance - support;
  if (range > 0) {
    const pctFromSupport = ((lastClose - support) / range) * 100;
    if (pctFromSupport <= 15) reasons.push(`Near 60-day support (${fmt(support, 2)}) — potential bounce zone.`);
    else if (pctFromSupport >= 85) reasons.push(`Near 60-day resistance (${fmt(resistance, 2)}) — breakout or rejection zone.`);
  }

  // 6. Model probability
  if (pred.prob_up != null) {
    const p = pred.direction === 'up' ? pred.prob_up : pred.prob_down;
    reasons.push(`ML model assigns ${fmt(p * 100, 0)}% probability to next-session ${pred.direction} move.`);
  }

  return reasons.slice(0, 5);
}

/** Composite score for sorting watchlist signals: strong buy = high positive, strong sell = high negative */
function compositeScore(pred: any): number {
  if (!pred?.model_available) return 0;
  const sign = pred.direction === 'up' ? 1 : -1;
  return sign * pred.confidence;
}

/* ------------------------------------------------------------------ */
/*  Component                                                         */
/* ------------------------------------------------------------------ */

export default function SignalsPanel() {
  const { symbol, setSymbol } = useStore();
  const { ohlcvData, predictions, loadPrediction, loadOHLCV } = useMarketDataContext();

  const meta = DEFAULT_SYMBOLS.find((s: any) => s.sym === symbol);
  const series = (ohlcvData[symbol] && ohlcvData[symbol].length > 0) ? ohlcvData[symbol] : (meta?.series || []);
  const closes = series.map((d: any) => d.c);
  const pred = predictions[symbol];

  // Load prediction for selected symbol
  useEffect(() => {
    loadPrediction(symbol);
  }, [symbol, loadPrediction]);

  // ── Strength label & reasons ──
  const strength = strengthLabel(pred);
  const reasons = useMemo(() => buildReasons(pred, closes), [pred, closes]);

  // ── Watchlist signals sorted by priority ──
  const watchlistSignals = useMemo(() => {
    return DEFAULT_SYMBOLS
      .map(s => ({
        sym: s.sym,
        name: s.name,
        pred: predictions[s.sym],
        strength: strengthLabel(predictions[s.sym]),
        score: compositeScore(predictions[s.sym]),
      }))
      .filter(s => s.pred?.model_available)
      .sort((a, b) => Math.abs(b.score) - Math.abs(a.score));
  }, [predictions]);

  // Also include items still loading
  const pendingSymbols = DEFAULT_SYMBOLS.filter(s => !predictions[s.sym]);

  // ── Entry / Target / Stop estimates ──
  const lastClose = closes.length > 0 ? closes[closes.length - 1] : null;
  const window = series.slice(-Math.min(60, series.length));
  const support = window.length > 0 ? Math.min(...window.map((d: any) => d.l)) : null;
  const resistance = window.length > 0 ? Math.max(...window.map((d: any) => d.h)) : null;

  const handleSymClick = (sym: string) => {
    setSymbol(sym);
    if (!ohlcvData[sym] || ohlcvData[sym].length === 0) {
      loadOHLCV(sym, '3M');
    }
    loadPrediction(sym);
  };

  return (
    <div className="signals">
      {/* ── PREDICTION (selected symbol) ── */}
      <div className="sig-section">
        <div className="sig-title">PREDICTION — {symbol}</div>
        {!pred || !pred.model_available ? (
          <div className="sig-note">{pred?.message || 'Loading prediction…'}</div>
        ) : (
          <>
            {/* Big signal badge */}
            <div className="pred-hero">
              <span className={'pred-badge ' + strength.cls}>{strength.label}</span>
              <span className="pred-conf">{fmt(pred.confidence * 100, 0)}% confidence</span>
            </div>

            {/* Confidence bar */}
            <div className="pred-conf-bar-wrap">
              <div className="pred-conf-bar">
                <div
                  className={'pred-conf-fill ' + strength.cls}
                  style={{ width: (pred.confidence * 100) + '%' }}
                />
              </div>
              <div className="pred-conf-labels">
                <span>0%</span>
                <span>50%</span>
                <span>100%</span>
              </div>
            </div>

            {/* Entry / Target / Stop */}
            {lastClose != null && support != null && resistance != null && (
              <div className="pred-levels">
                <div className="sig-row">
                  <span className="k">Entry</span>
                  <span className="v">{fmt(lastClose, 2)}</span>
                </div>
                <div className="sig-row">
                  <span className="k">Target</span>
                  <span className="v up-text">
                    {pred.direction === 'up' ? fmt(resistance, 2) : fmt(support, 2)}
                  </span>
                </div>
                <div className="sig-row">
                  <span className="k">Stop Loss</span>
                  <span className="v down-text">
                    {pred.direction === 'up' ? fmt(support, 2) : fmt(resistance, 2)}
                  </span>
                </div>
              </div>
            )}

            {/* Prob up / down */}
            <div className="pred-probs">
              <div className="sig-row">
                <span className="k">Prob. Up / Down</span>
                <span className="v">{fmt(pred.prob_up * 100, 0)}% / {fmt(pred.prob_down * 100, 0)}%</span>
              </div>
              {pred.holdout_accuracy != null && (
                <div className="sig-row">
                  <span className="k">Model accuracy</span>
                  <span className="v">{fmt(pred.holdout_accuracy * 100, 1)}%</span>
                </div>
              )}
            </div>
          </>
        )}
      </div>

      {/* ── JUSTIFICATION ── */}
      {pred?.model_available && (
        <div className="sig-section">
          <div className="sig-title">WHY THIS SIGNAL</div>
          <ul className="pred-reasons">
            {reasons.map((r, i) => (
              <li key={i} className="pred-reason">{r}</li>
            ))}
          </ul>
          <div className="sig-note" style={{ marginTop: 8 }}>
            RandomForest on {pred.n_training_samples} bars • features: return, SMA-gap, RSI, MACD
          </div>
        </div>
      )}

      {/* ── WATCHLIST SIGNALS ── */}
      <div className="sig-section">
        <div className="sig-title">WATCHLIST SIGNALS</div>
        <div className="sig-note" style={{ marginBottom: 8, fontSize: '10.5px' }}>
          Sorted by signal strength — click to view
        </div>
        <div className="wl-signals-list">
          {watchlistSignals.map(s => (
            <button
              key={s.sym}
              className={'wl-signal-row' + (s.sym === symbol ? ' active' : '')}
              onClick={() => handleSymClick(s.sym)}
            >
              <div className="wl-signal-left">
                <span className="wl-signal-sym">{s.sym}</span>
                <span className="wl-signal-name">{s.name}</span>
              </div>
              <div className="wl-signal-right">
                <span className={'sig-badge ' + s.strength.cls}>{s.strength.label}</span>
                <span className="wl-signal-conf">{fmt(s.pred.confidence * 100, 0)}%</span>
              </div>
            </button>
          ))}
          {pendingSymbols.map(s => (
            <button
              key={s.sym}
              className={'wl-signal-row dimmed' + (s.sym === symbol ? ' active' : '')}
              onClick={() => handleSymClick(s.sym)}
            >
              <div className="wl-signal-left">
                <span className="wl-signal-sym">{s.sym}</span>
                <span className="wl-signal-name">{s.name}</span>
              </div>
              <div className="wl-signal-right">
                <span className="sig-badge neutral">Loading…</span>
              </div>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
