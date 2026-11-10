export interface OHLCV {
  o: number;
  h: number;
  l: number;
  c: number;
  v: number;
}

export interface SymbolData {
  sym: string;
  name: string;
  base: number;
  vol: number;
  baseVol: number;
  series: OHLCV[];
}

export interface Timeframe {
  k: string;
  n: number;
}

export interface AppState {
  symbol: string;
  tf: string;
}
