import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

const http = axios.create({ baseURL: API_BASE, timeout: 20000 });

// ---------------------------------------------------------------------------
// Market data
// ---------------------------------------------------------------------------

export async function fetchSymbols(): Promise<string[]> {
  try {
    const res = await http.get('/api/market/symbols');
    return res.data.symbols || [];
  } catch {
    return [];
  }
}

export async function fetchOHLCV(symbol: string, timeframe: string = '3M') {
  try {
    const res = await http.get(`/api/market/ohlcv/${symbol}`, { params: { timeframe } });
    return res.data;
  } catch {
    return null;
  }
}

export async function fetchSummary(symbol: string, timeframe: string = '3M') {
  try {
    const res = await http.get(`/api/market/ohlcv/${symbol}/summary`, { params: { timeframe } });
    return res.data;
  } catch {
    return null;
  }
}

export async function fetchPrediction(symbol: string, timeframe: string = '1Y') {
  try {
    const res = await http.get(`/api/predict/${symbol}`, { params: { timeframe } });
    return res.data;
  } catch {
    return null;
  }
}

export async function fetchMarketWatch(limit: number = 100): Promise<any[]> {
  try {
    const res = await http.get('/api/market/market-watch', { params: { limit } });
    return res.data.data || [];
  } catch {
    return [];
  }
}

export async function fetchQuote(symbol: string) {
  try {
    const res = await http.get(`/api/market/quote/${symbol}`);
    return res.data.quote || null;
  } catch {
    return null;
  }
}

export async function fetchHealth() {
  try {
    const res = await http.get('/api/market/health');
    return res.data;
  } catch {
    return null;
  }
}

// ---------------------------------------------------------------------------
// Trading
// ---------------------------------------------------------------------------

export interface OrderRequest {
  symbol: string;
  side: 'buy' | 'sell';
  qty: number;
  order_type?: 'market' | 'limit' | 'stop' | 'stop_limit';
  limit_price?: number;
  stop_price?: number;
}

export async function fetchTradingStatus() {
  try {
    const res = await http.get('/api/trading/status');
    return res.data;
  } catch {
    return { connected: false, paper_mode: true, live_trading_allowed: false };
  }
}

export async function fetchAccount() {
  try {
    const res = await http.get('/api/trading/account');
    return res.data;
  } catch {
    return null;
  }
}

export async function fetchPositions(): Promise<any[]> {
  try {
    const res = await http.get('/api/trading/positions');
    return res.data.positions || [];
  } catch {
    return [];
  }
}

export async function fetchOrders(status?: string): Promise<any[]> {
  try {
    const res = await http.get('/api/trading/orders', { params: status ? { status } : {} });
    return res.data.orders || [];
  } catch {
    return [];
  }
}

/** Submit an order. Throws with the backend's message so the UI can show it. */
export async function submitOrder(order: OrderRequest) {
  try {
    const res = await http.post('/api/trading/orders', order);
    return res.data;
  } catch (err: any) {
    throw new Error(err?.response?.data?.detail || 'Order failed');
  }
}

export async function cancelOrder(orderId: string) {
  try {
    const res = await http.delete(`/api/trading/orders/${orderId}`);
    return res.data;
  } catch (err: any) {
    throw new Error(err?.response?.data?.detail || 'Cancel failed');
  }
}
