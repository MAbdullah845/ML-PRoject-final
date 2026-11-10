export function sma(closes: number[], period: number): (number | null)[] {
  const out = new Array(closes.length).fill(null);
  for (let i = period - 1; i < closes.length; i++) {
    let sum = 0;
    for (let j = i - period + 1; j <= i; j++) sum += closes[j];
    out[i] = sum / period;
  }
  return out;
}

export function ema(values: number[], period: number): number[] {
  const k = 2 / (period + 1);
  const out = new Array(values.length).fill(null);
  out[0] = values[0];
  for (let i = 1; i < values.length; i++) {
    out[i] = values[i] * k + out[i - 1] * (1 - k);
  }
  return out;
}

export function rsi(closes: number[], period = 14): (number | null)[] {
  const out = new Array(closes.length).fill(null);
  if (closes.length <= period) return out;
  let gain = 0, loss = 0;
  for (let i = 1; i <= period; i++) {
    const d = closes[i] - closes[i - 1];
    if (d >= 0) gain += d; else loss -= d;
  }
  let avgGain = gain / period, avgLoss = loss / period;
  out[period] = 100 - 100 / (1 + (avgLoss === 0 ? 100 : avgGain / avgLoss));
  for (let i = period + 1; i < closes.length; i++) {
    const d = closes[i] - closes[i - 1];
    const g = d > 0 ? d : 0, l = d < 0 ? -d : 0;
    avgGain = (avgGain * (period - 1) + g) / period;
    avgLoss = (avgLoss * (period - 1) + l) / period;
    const rs = avgLoss === 0 ? 100 : avgGain / avgLoss;
    out[i] = 100 - 100 / (1 + rs);
  }
  return out;
}

export function macdHist(closes: number[]): number[] {
  const fast = ema(closes, 12), slow = ema(closes, 26);
  const macdLine = closes.map((_, i) => fast[i] - slow[i]);
  const signal = ema(macdLine, 9);
  return macdLine.map((m, i) => m - signal[i]);
}

export function fmt(n: number, d = 2): string {
  return Number(n).toLocaleString('en-US', { minimumFractionDigits: d, maximumFractionDigits: d });
}

export function fmtVol(n: number): string {
  return n >= 1e6 ? (n / 1e6).toFixed(2) + 'M' : n >= 1e3 ? (n / 1e3).toFixed(1) + 'K' : String(n);
}

export function pctChange(series: { o: number; c: number }[]): number {
  const c0 = series[series.length - 2].o, c1 = series[series.length - 1].c;
  return ((c1 - c0) / c0) * 100;
}

export function sparkPath(closes: number[]): string {
  const c = closes.slice(-30);
  const max = Math.max(...c), min = Math.min(...c);
  const w = 46, h = 20;
  return c.map((v, i) => {
    const x = (i / (c.length - 1)) * w;
    const y = h - ((v - min) / ((max - min) || 1)) * h;
    return (i === 0 ? 'M' : 'L') + x.toFixed(1) + ',' + y.toFixed(1);
  }).join(' ');
}

export function slice(series: { o: number; h: number; l: number; c: number; v: number }[], n: number) {
  return series.slice(series.length - n);
}

export function hashStr(s: string): number {
  let h = 1779033703 ^ s.length;
  for (let i = 0; i < s.length; i++) {
    h = Math.imul(h ^ s.charCodeAt(i), 3432918353);
    h = h << 13 | h >>> 19;
  }
  return (h ^ h >>> 16) >>> 0;
}

export function mulberry32(a: number): () => number {
  return function () {
    a |= 0;
    a = a + 0x6D2B79F5 | 0;
    let t = Math.imul(a ^ a >>> 15, 1 | a);
    t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
    return ((t ^ t >>> 14) >>> 0) / 4294967296;
  };
}

export function genSeries(seedKey: string, base: number, n: number, vol: number, baseVol: number) {
  const rng = mulberry32(hashStr(seedKey));
  let price = base;
  const out = [];
  for (let i = 0; i < n; i++) {
    const drift = (rng() - 0.48) * vol;
    const open = price;
    const close = Math.max(0.5, open * (1 + drift));
    const high = Math.max(open, close) * (1 + rng() * vol * 0.55);
    const low = Math.min(open, close) * (1 - rng() * vol * 0.55);
    const v = Math.round((rng() * 0.6 + 0.45) * baseVol);
    out.push({ o: open, h: high, l: low, c: close, v });
    price = close;
  }
  return out;
}
