import { genSeries, hashStr, mulberry32 } from '../utils/indicators';
import type { SymbolData } from '../types';

const SERIES_LEN = 264;

export const DEFAULT_SYMBOLS: SymbolData[] = [
  { sym: 'OGDC', name: 'Oil & Gas Development Co.', base: 98.4, vol: 0.026, baseVol: 8200000, series: [] },
  { sym: 'UBL', name: 'United Bank Limited', base: 412.9, vol: 0.022, baseVol: 1200000, series: [] },
  { sym: 'LUCK', name: 'Lucky Cement Ltd.', base: 781, vol: 0.021, baseVol: 900000, series: [] },
  { sym: 'ENGRO', name: 'Engro Corporation', base: 311, vol: 0.019, baseVol: 1150000, series: [] },
  { sym: 'HBL', name: 'Habib Bank Ltd.', base: 118, vol: 0.020, baseVol: 3050000, series: [] },
  { sym: 'PSO', name: 'Pakistan State Oil Co.', base: 212, vol: 0.031, baseVol: 2450000, series: [] },
  { sym: 'MEBL', name: 'Meezan Bank Ltd.', base: 166, vol: 0.021, baseVol: 1980000, series: [] },
  { sym: 'FFC', name: 'Fauji Fertilizer Co.', base: 135, vol: 0.017, baseVol: 1750000, series: [] },
  { sym: 'PPL', name: 'Pakistan Petroleum Ltd.', base: 112, vol: 0.025, baseVol: 3950000, series: [] },
];

DEFAULT_SYMBOLS.forEach(s => {
  s.series = genSeries(s.sym, s.base, SERIES_LEN, s.vol, s.baseVol);
});

export { SERIES_LEN };
export default DEFAULT_SYMBOLS;
