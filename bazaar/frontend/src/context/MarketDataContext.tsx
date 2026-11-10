import { createContext, useContext, useState, useCallback, useEffect, useRef } from 'react';
import type { ReactNode } from 'react';
import { fetchSymbols, fetchOHLCV, fetchPrediction } from '../services/api';
import { DEFAULT_SYMBOLS } from '../data/symbols';
import type { OHLCV } from '../types';

interface MarketDataContextValue {
  symbols: string[];
  ohlcvData: Record<string, OHLCV[]>;
  predictions: Record<string, any>;
  loading: boolean;
  loadOHLCV: (sym: string, tf?: string) => Promise<void>;
  loadPrediction: (sym: string) => Promise<void>;
}

const MarketDataContext = createContext<MarketDataContextValue | null>(null);

/**
 * Single shared fetch layer for the whole app. Without this, each component
 * that called the old per-component useMarketData() hook got its own,
 * independently-empty copy of the data — so only whichever component
 * happened to trigger a fetch (the chart) ever showed live prices, while
 * the watchlist and ticker strip stayed on generated mock numbers forever.
 */
export function MarketDataProvider({ children }: { children: ReactNode }) {
  const [symbols, setSymbols] = useState<string[]>(DEFAULT_SYMBOLS.map(s => s.sym));
  const [ohlcvData, setOhlcvData] = useState<Record<string, OHLCV[]>>({});
  const [predictions, setPredictions] = useState<Record<string, any>>({});
  const [loading, setLoading] = useState(false);
  const primed = useRef(false);

  const loadOHLCV = useCallback(async (sym: string, tf: string = '3M') => {
    const data = await fetchOHLCV(sym, tf);
    if (data && data.data) {
      const mapped: OHLCV[] = data.data.map((d: any) => ({
        o: d.open, h: d.high, l: d.low, c: d.close, v: d.volume,
      }));
      setOhlcvData(prev => ({ ...prev, [sym]: mapped }));
    }
  }, []);

  const loadPrediction = useCallback(async (sym: string) => {
    const pred = await fetchPrediction(sym);
    if (pred) {
      setPredictions(prev => ({ ...prev, [sym]: pred }));
    }
  }, []);

  // On first mount: fetch the live symbol universe, then live OHLCV for
  // every watchlist row so prices/sparklines are real everywhere, not just
  // on whichever symbol is currently selected in the chart.
  useEffect(() => {
    if (primed.current) return;
    primed.current = true;

    (async () => {
      setLoading(true);
      const liveSymbols = await fetchSymbols();
      if (liveSymbols.length > 0) setSymbols(liveSymbols);

      await Promise.all(DEFAULT_SYMBOLS.map(s => loadOHLCV(s.sym, '3M')));

      // Load predictions for every watchlist symbol so the signals panel
      // can rank them by strength on first load.
      await Promise.all(DEFAULT_SYMBOLS.map(s => loadPrediction(s.sym)));
      setLoading(false);
    })();
  }, [loadOHLCV, loadPrediction]);

  return (
    <MarketDataContext.Provider value={{ symbols, ohlcvData, predictions, loading, loadOHLCV, loadPrediction }}>
      {children}
    </MarketDataContext.Provider>
  );
}

export function useMarketDataContext(): MarketDataContextValue {
  const ctx = useContext(MarketDataContext);
  if (!ctx) {
    throw new Error('useMarketDataContext must be used inside <MarketDataProvider>');
  }
  return ctx;
}
