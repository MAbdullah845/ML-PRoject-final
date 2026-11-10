import { useRef, useCallback, useState, useEffect } from 'react';
import { useStore } from '../../store/useStore';
import { useMarketDataContext } from '../../context/MarketDataContext';
import { fmt, pctChange, sma, rsi, macdHist, fmtVol } from '../../utils/indicators';
import { DEFAULT_SYMBOLS } from '../../data/symbols';

const TIMEFRAMES = ['1M', '3M', '6M', '1Y'];
const TF_MAP: Record<string, number> = { '1M': 22, '3M': 66, '6M': 132, '1Y': 264 };

function buildPriceSvg(data: any[], tfKey: string) {
  const W = 1000, H = 300, padTop = 14, padBottom = 14, rightGutter = 46;
  const plotW = W - rightGutter;
  const n = data.length;
  const step = plotW / n;
  const cw = Math.max(1.4, step * 0.62);
  const gap = (step - cw) / 2;
  const highs = data.map((d: any) => d.h), lows = data.map((d: any) => d.l);
  const max = Math.max(...highs) * 1.004, min = Math.min(...lows) * 0.996;
  const y = (p: number) => padTop + (max - p) / (max - min) * (H - padTop - padBottom);
  const closes = data.map((d: any) => d.c);
  const sma20 = sma(closes, 20);

  let grid = '';
  for (let i = 0; i <= 4; i++) {
    const py = padTop + i * (H - padTop - padBottom) / 4;
    const priceAtY = max - (i / 4) * (max - min);
    grid += '<line x1="0" y1="' + py.toFixed(1) + '" x2="' + plotW + '" y2="' + py.toFixed(1) + '" stroke="var(--line-soft)" strokeWidth="1"/>';
    grid += '<text x="' + (plotW + 8) + '" y="' + ((py + 3).toFixed(1)) + '" fill="var(--text-faint)" fontSize="9.5" fontFamily="IBM Plex Mono, monospace">' + fmt(priceAtY, 1) + '</text>';
  }

  let candles = '';
  data.forEach((d: any, i: number) => {
    const x = i * step + gap;
    const up = d.c >= d.o;
    const color = up ? 'var(--up)' : 'var(--down)';
    const yO = y(d.o), yC = y(d.c), yH = y(d.h), yL = y(d.l);
    const bodyTop = Math.min(yO, yC), bodyH = Math.max(1.1, Math.abs(yC - yO));
    candles += '<line x1="' + (x + cw / 2).toFixed(2) + '" y1="' + yH.toFixed(2) + '" x2="' + (x + cw / 2).toFixed(2) + '" y2="' + yL.toFixed(2) + '" stroke="' + color + '" strokeWidth="1"/>';
    candles += '<rect x="' + x.toFixed(2) + '" y="' + bodyTop.toFixed(2) + '" width="' + cw.toFixed(2) + '" height="' + bodyH.toFixed(2) + '" fill="' + color + '"/>';
  });

  let smaPath = '', started = false;
  data.forEach((_: any, i: number) => {
    if (sma20[i] == null) return;
    const px = i * step + gap + cw / 2, py = y(sma20[i]);
    smaPath += (started ? 'L' : 'M') + px.toFixed(2) + ',' + py.toFixed(2) + ' ';
    started = true;
  });

  return grid + candles + '<path d="' + smaPath + '" fill="none" stroke="var(--gold)" strokeWidth="1.4" strokeDasharray="5 3" opacity="0.85"/>';
}

function buildVolumeSvg(data: any[]) {
  const W = 1000, H = 90, rightGutter = 46, plotW = W - rightGutter;
  const n = data.length;
  const step = plotW / n, cw = Math.max(1.4, step * 0.62), gap = (step - cw) / 2;
  const max = Math.max(...data.map((d: any) => d.v)) * 1.1;
  let bars = '';
  data.forEach((d: any, i: number) => {
    const x = i * step + gap;
    const h = (d.v / max) * (H - 6);
    const up = d.c >= d.o;
    bars += '<rect x="' + x.toFixed(2) + '" y="' + (H - h).toFixed(2) + '" width="' + cw.toFixed(2) + '" height="' + h.toFixed(2) + '" fill="' + (up ? 'var(--up)' : 'var(--down)') + '"/>';
  });
  return bars;
}

function buildRsiSvg(data: any[]) {
  const W = 1000, H = 90, rightGutter = 46, plotW = W - rightGutter;
  const n = data.length;
  const step = plotW / n;
  const closes = data.map((d: any) => d.c);
  const rsiArr = rsi(closes, 14);
  const y = (v: number) => 6 + (100 - v) / 100 * (H - 12);
  const y70 = y(70), y30 = y(30);
  let lines = '<line x1="0" y1="' + y70.toFixed(1) + '" x2="' + plotW + '" y2="' + y70.toFixed(1) + '" stroke="var(--down)" strokeWidth="1" strokeDasharray="3 3" opacity="0.45"/>'
    + '<line x1="0" y1="' + y30.toFixed(1) + '" x2="' + plotW + '" y2="' + y30.toFixed(1) + '" stroke="var(--up)" strokeWidth="1" strokeDasharray="3 3" opacity="0.45"/>'
    + '<text x="' + (plotW + 8) + '" y="' + (y70 + 3).toFixed(1) + '" fill="var(--text-faint)" fontSize="9" fontFamily="IBM Plex Mono, monospace">70</text>'
    + '<text x="' + (plotW + 8) + '" y="' + (y30 + 3).toFixed(1) + '" fill="var(--text-faint)" fontSize="9" fontFamily="IBM Plex Mono, monospace">30</text>';
  let path = '', started = false;
  rsiArr.forEach((v: number | null, i: number) => {
    if (v == null) return;
    const px = i * step + step / 2, py = y(v);
    path += (started ? 'L' : 'M') + px.toFixed(2) + ',' + py.toFixed(2) + ' ';
    started = true;
  });
  return lines + '<path d="' + path + '" fill="none" stroke="var(--gold)" strokeWidth="1.4"/>';
}

function buildMacdSvg(data: any[]) {
  const W = 1000, H = 90, rightGutter = 46, plotW = W - rightGutter;
  const n = data.length;
  const step = plotW / n, cw = Math.max(1.2, step * 0.55), gap = (step - cw) / 2;
  const closes = data.map((d: any) => d.c);
  const hist = macdHist(closes);
  const maxAbs = Math.max(0.001, ...hist.map((v: number) => Math.abs(v))) * 1.15;
  const mid = H / 2;
  let bars = '<line x1="0" y1="' + mid + '" x2="' + plotW + '" y2="' + mid + '" stroke="var(--line)" strokeWidth="1"/>';
  hist.forEach((v: number, i: number) => {
    const x = i * step + gap;
    const h = (Math.abs(v) / maxAbs) * (mid - 6);
    const up = v >= 0;
    const yTop = up ? mid - h : mid;
    bars += '<rect x="' + x.toFixed(2) + '" y="' + yTop.toFixed(2) + '" width="' + cw.toFixed(2) + '" height="' + Math.max(1, h).toFixed(2) + '" fill="' + (up ? 'var(--up)' : 'var(--down)') + '" opacity="0.75"/>';
  });
  return bars;
}

export default function Chart() {
  const { symbol, tf } = useStore();
  const { ohlcvData, loadOHLCV } = useMarketDataContext();
  const meta = DEFAULT_SYMBOLS.find((s: any) => s.sym === symbol);
  const n = tf === '1M' ? 22 : tf === '3M' ? 66 : tf === '6M' ? 132 : 264;
  const apiData = ohlcvData[symbol];
  const data = (apiData && apiData.length > 0) ? apiData.slice(-n) : (meta?.series.slice(meta.series.length - n) || []);

  const last = data[data.length - 1];
  const prev = data[data.length - 2];
  const chg = prev ? ((last.c - prev.o) / prev.o) * 100 : 0;
  const up = chg >= 0;

  const closes = data.map((d: any) => d.c);
  const sma20Val = sma(closes, 20);
  const lastSma = sma20Val[sma20Val.length - 1];

  const stackRef = useRef<HTMLDivElement>(null);
  const crosshairRef = useRef<HTMLDivElement>(null);
  const [tooltip, setTooltip] = useState<{ x: number; y: number; visible: boolean; d: any; idx: number } | null>(null);

  useEffect(() => {
    loadOHLCV(symbol, tf);
  }, [symbol, tf, loadOHLCV]);

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    if (!stackRef.current || data.length === 0) return;
    const rect = stackRef.current.getBoundingClientRect();
    const xRatio = Math.min(1, Math.max(0, (e.clientX - rect.left) / rect.width));
    const idx = Math.min(data.length - 1, Math.max(0, Math.floor(xRatio * data.length)));
    const d = data[idx];
    const up = d.c >= d.o;
    const crosshair = crosshairRef.current;
    if (crosshair) {
      crosshair.style.left = (e.clientX - rect.left) + 'px';
      crosshair.style.opacity = '1';
    }
    setTooltip({ x: e.clientX, y: e.clientY, visible: true, d, idx });
  }, [data]);

  const handleMouseLeave = useCallback(() => {
    const crosshair = crosshairRef.current;
    if (crosshair) crosshair.style.opacity = '0';
    setTooltip(null);
  }, []);

  return (
    <div className="main">
      <div className="main-header">
        <div className="quote-block">
          <span className="quote-sym serif">{symbol}</span>
          <span className="quote-name">{meta?.name}</span>
          <span className="quote-price mono">PKR {fmt(last?.c || 0, 2)}</span>
          <span className={'quote-chg mono ' + (up ? 'up' : 'down')}>
            {up ? '+' : ''}{fmt(chg, 2)}%
          </span>
        </div>
        <div className="tf-tabs">
          {TIMEFRAMES.map((t: string) => (
            <button
              key={t}
              className={'tf-tab' + (t === tf ? ' active' : '')}
              onClick={() => useStore.getState().setTimeframe(t)}
            >
              {t}
            </button>
          ))}
        </div>
      </div>
      <div className="chart-stack" id="chartStack" ref={stackRef}
        onMouseMove={handleMouseMove} onMouseLeave={handleMouseLeave}>
        <div className="crosshair-v" id="crosshair" ref={crosshairRef} />
        <div className="chart-pane price">
          <span className="pane-label">PRICE · SMA 20</span>
          <svg id="svgPrice" viewBox="0 0 1000 300" preserveAspectRatio="none"
            dangerouslySetInnerHTML={{ __html: buildPriceSvg(data, tf) }} />
        </div>
        <div className="chart-pane volume">
          <span className="pane-label">VOLUME</span>
          <svg id="svgVolume" viewBox="0 0 1000 90" preserveAspectRatio="none"
            dangerouslySetInnerHTML={{ __html: buildVolumeSvg(data) }} />
        </div>
        <div className="chart-pane rsi">
          <span className="pane-label">RSI 14</span>
          <svg id="svgRsi" viewBox="0 0 1000 90" preserveAspectRatio="none"
            dangerouslySetInnerHTML={{ __html: buildRsiSvg(data) }} />
        </div>
        <div className="chart-pane macd">
          <span className="pane-label">MACD 12,26,9</span>
          <svg id="svgMacd" viewBox="0 0 1000 90" preserveAspectRatio="none"
            dangerouslySetInnerHTML={{ __html: buildMacdSvg(data) }} />
        </div>
        {tooltip && tooltip.visible && (
          <div className="tooltip" style={{ left: tooltip.x + 14, top: tooltip.y + 10, opacity: 1 }}>
            <div><b>{symbol}</b> · bar {tooltip.idx + 1}/{data.length}</div>
            <div>O <span className={tooltip.d.c >= tooltip.d.o ? 'tt-up' : 'tt-down'}>{fmt(tooltip.d.o, 2)}</span>&nbsp;&nbsp;H {fmt(tooltip.d.h, 2)}</div>
            <div>L {fmt(tooltip.d.l, 2)}&nbsp;&nbsp;C <span className={tooltip.d.c >= tooltip.d.o ? 'tt-up' : 'tt-down'}>{fmt(tooltip.d.c, 2)}</span></div>
            <div>Vol {fmtVol(tooltip.d.v)}</div>
          </div>
        )}
      </div>
    </div>
  );
}
