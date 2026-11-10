import { useStore } from '../store/useStore';
import { DEFAULT_SYMBOLS } from '../data/symbols';
import { fmt, pctChange, sparkPath } from '../utils/indicators';
import { useMarketDataContext } from '../context/MarketDataContext';

export default function Watchlist() {
  const { symbol, setSymbol } = useStore();
  const { ohlcvData } = useMarketDataContext();

  const symbols = DEFAULT_SYMBOLS;

  return (
    <div className="watchlist">
      <div className="panel-heading">
        <span>WATCHLIST</span>
        <span id="wlCount">{symbols.length}/{symbols.length}</span>
      </div>
      <div id="wlRows">
        {symbols.map(s => {
          const series = ohlcvData[s.sym] || s.series;
          const chg = series.length > 1 ? pctChange(series) : 0;
          const up = chg >= 0;
          return (
            <button
              key={s.sym}
              className={'wl-row' + (s.sym === symbol ? ' active' : '')}
              onClick={() => setSymbol(s.sym)}
            >
              <span className="wl-left">
                <span className="wl-sym">{s.sym}</span>
                <span className="wl-name">{s.name}</span>
              </span>
              <svg className="wl-spark" viewBox="0 0 46 20" preserveAspectRatio="none">
                <path d={sparkPath(series.map((d: any) => d.c))} fill="none" stroke={up ? 'var(--up)' : 'var(--down)'} strokeWidth="1.3" />
              </svg>
              <span className="wl-right">
                <span className="wl-price mono">{fmt(series[series.length - 1].c, 2)}</span>
                <span className="wl-chg mono" style={{ color: up ? 'var(--up)' : 'var(--down)' }}>
                  {up ? '+' : ''}{fmt(chg, 2)}%
                </span>
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
