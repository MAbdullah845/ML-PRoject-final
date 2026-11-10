import { useEffect, useState, useRef, useMemo } from 'react';
import { useStore } from '../store/useStore';
import { useMarketDataContext } from '../context/MarketDataContext';
import { genSeries, hashStr, mulberry32, fmt, pctChange } from '../utils/indicators';

const INDEX_SERIES = genSeries('KSE100', 78650, 264, 0.012, 0);

function renderIndex() {
  const last = INDEX_SERIES[INDEX_SERIES.length - 1].c;
  const chg = pctChange(INDEX_SERIES);
  const up = chg >= 0;
  return (
    <div className="index-widget mono">
      <span className="name">KSE-100</span>
      <span className="val">{fmt(last, 0)}</span>
      <span style={{ color: up ? 'var(--up)' : 'var(--down)' }}>
        {up ? '+' : ''}{fmt(chg, 2)}%
      </span>
    </div>
  );
}

function Clock() {
  const [time, setTime] = useState('');
  const [marketOpen, setMarketOpen] = useState(false);

  useEffect(() => {
    const interval = setInterval(() => {
      const now = new Date();
      const parts = new Intl.DateTimeFormat('en-GB', {
        timeZone: 'Asia/Karachi',
        hour: '2-digit', minute: '2-digit', second: '2-digit',
        hour12: false, weekday: 'short'
      }).formatToParts(now);
      const map: Record<string, string> = {};
      parts.forEach(p => map[p.type] = p.value);
      const h = parseInt(map.hour, 10), m = parseInt(map.minute, 10);
      const mins = h * 60 + m;
      const isWeekday = !['Sat', 'Sun'].includes(map.weekday);
      const open = isWeekday && mins >= 570 && mins <= 930;
      setTime(map.hour + ':' + map.minute + ':' + map.second + ' PKT');
      setMarketOpen(open);
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="clock-widget">
      <span className={'status-dot' + (marketOpen ? '' : ' closed')} />
      <span>{marketOpen ? 'Market open' : 'Market closed'}</span>
      <span className="mono">{time}</span>
    </div>
  );
}

export default function TopBar() {
  const { search, setSearch, symbol, setSymbol } = useStore();
  const { symbols, loadOHLCV, loadPrediction } = useMarketDataContext();
  const [open, setOpen] = useState(false);
  const [activeIdx, setActiveIdx] = useState(0);
  const boxRef = useRef<HTMLDivElement>(null);

  const matches = useMemo(() => {
    const q = search.trim().toUpperCase();
    if (!q) return [];
    return symbols.filter(s => s.toUpperCase().includes(q)).slice(0, 8);
  }, [search, symbols]);

  useEffect(() => setActiveIdx(0), [search]);

  useEffect(() => {
    function onClickOutside(e: MouseEvent) {
      if (boxRef.current && !boxRef.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener('mousedown', onClickOutside);
    return () => document.removeEventListener('mousedown', onClickOutside);
  }, []);

  const selectSymbol = (sym: string) => {
    setSymbol(sym);
    loadOHLCV(sym, '3M');
    loadPrediction(sym);
    setSearch('');
    setOpen(false);
  };

  const onKeyDown = (e: React.KeyboardEvent) => {
    if (!open || matches.length === 0) return;
    if (e.key === 'ArrowDown') { e.preventDefault(); setActiveIdx(i => Math.min(i + 1, matches.length - 1)); }
    else if (e.key === 'ArrowUp') { e.preventDefault(); setActiveIdx(i => Math.max(i - 1, 0)); }
    else if (e.key === 'Enter') { e.preventDefault(); selectSymbol(matches[activeIdx]); }
    else if (e.key === 'Escape') { setOpen(false); }
  };

  return (
    <div className="topbar">
      <div className="brand">
        <span className="mark serif">BAZAAR<em>.</em></span>
        <span className="sub">PSX TERMINAL · TECHNICAL ANALYSIS</span>
      </div>
      <div className="topbar-right">
        {renderIndex()}
        <Clock />
        <div className="search-wrap" ref={boxRef}>
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="11" cy="11" r="7" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
          <input id="searchInput" type="text" placeholder="Search any PSX symbol" autoComplete="off"
            value={search}
            onChange={(e) => { setSearch(e.target.value); setOpen(true); }}
            onFocus={() => { if (search) setOpen(true); }}
            onKeyDown={onKeyDown}
          />
          {open && search && (
            <div className="search-dropdown">
              {matches.length === 0 ? (
                <div className="sd-empty">No matching symbol</div>
              ) : (
                matches.map((s, i) => (
                  <div
                    key={s}
                    className={'sd-item' + (i === activeIdx ? ' active' : '')}
                    onMouseEnter={() => setActiveIdx(i)}
                    onClick={() => selectSymbol(s)}
                  >
                    <span className="sd-sym">{s}</span>
                    {s === symbol && <span className="sd-hint">current</span>}
                  </div>
                ))
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
