import { useMemo } from 'react';
import { DEFAULT_SYMBOLS } from '../data/symbols';
import { fmt, pctChange } from '../utils/indicators';
import { useStore } from '../store/useStore';
import { useMarketDataContext } from '../context/MarketDataContext';

export default function TickerStrip() {
  const { symbol } = useStore();
  const { ohlcvData } = useMarketDataContext();

  const rows = useMemo(() => {
    return DEFAULT_SYMBOLS.map(s => {
      const series = ohlcvData[s.sym] || s.series;
      const chg = series.length > 1 ? pctChange(series) : 0;
      const up = chg >= 0;
      return (
        <span className="ticker-item" key={s.sym}>
          <b>{s.sym}</b>
          <span>{fmt(series[series.length - 1].c, 2)}</span>
          <span className={up ? 'up' : 'down'}>
            {up ? '▲' : '▼'} {fmt(Math.abs(chg), 2)}%
          </span>
        </span>
      );
    });
  }, [ohlcvData]);

  return (
    <div className="ticker-strip">
      <div className="ticker-track mono">
        {rows}{rows}
      </div>
    </div>
  );
}
