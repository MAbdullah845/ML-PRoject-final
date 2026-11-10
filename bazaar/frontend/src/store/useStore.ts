import { create } from 'zustand';
import type { AppState } from '../types';

interface Store extends AppState {
  setSymbol: (symbol: string) => void;
  setTimeframe: (tf: string) => void;
  search: string;
  setSearch: (search: string) => void;
}

export const useStore = create<Store>((set) => ({
  symbol: 'OGDC',
  tf: '3M',
  search: '',
  setSymbol: (symbol) => set({ symbol }),
  setTimeframe: (tf) => set({ tf }),
  setSearch: (search) => set({ search }),
}));
