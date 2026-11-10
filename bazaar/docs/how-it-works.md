# How Data Flows from API to Frontend

## Complete Data Flow

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  PSX Data    │────►│  Backend     │────►│  Frontend    │────►│  Browser     │
│  Provider    │     │  (FastAPI)   │     │  (React)     │     │  (UI)        │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
       │                    │                    │                     │
       ▼                    ▼                    ▼                     ▼
  Raw Market Data    Normalized OHLCV    Processed Signals    Candlestick Chart
  (Ticks/Quotes)     (pandas DataFrame)  (RSI, MACD, SMA)    + Watchlist
```

## Step-by-Step Flow

### 1. Data Ingestion
1. Backend fetches OHLCV data from PSX market-data API
2. Data is normalized into the OHLCV model: `timestamp, open, high, low, close, volume, symbol`
3. Stored in PostgreSQL for persistence and caching

### 2. Data Processing
1. Frontend requests data via `GET /api/market/ohlcv/{symbol}?timeframe=3M`
2. Backend generates/slices OHLCV data using Pandas/NumPy
3. Technical indicators are calculated:
   - **SMA 20**: Simple Moving Average over 20 periods
   - **RSI 14**: Relative Strength Index over 14 periods
   - **MACD**: Moving Average Convergence Divergence (12,26,9)
4. Data returned as JSON

### 3. Frontend Rendering
1. Zustand store updates with new data
2. React components re-render based on store state
3. Chart component builds SVG elements programmatically:
   - **Price Pane**: Candlestick chart + SMA20 overlay line
   - **Volume Pane**: Volume bars colored by price direction
   - **RSI Pane**: RSI line with overbought/oversold levels
   - **MACD Pane**: Histogram bars for MACD signal

### 4. Signal Generation
1. SignalsPanel reads latest indicator values
2. Compares price to SMA20 for trend direction
3. Checks RSI thresholds (70/30) for overbought/oversold
4. Calculates support/resistance from 60-day window
5. Generates human-readable analysis note

### 5. User Interaction
1. User searches for a symbol → Watchlist filters → Zustand updates → Chart re-renders
2. User selects timeframe → Zustand updates → Data reslices → Chart re-renders
3. User hovers chart → Crosshair + tooltip shows OHLCV data for selected bar

## API Layer Design

The backend uses a clean API layer so the PSX data provider can be replaced:

```
app/api/market_data.py  ← Routes
app/data/ohlcv_service.py ← Data generation/processing (SWAP HERE)
```

To swap PSX providers:
1. Create `app/data/new_provider.py` with the same interface
2. Update `app/data/ohlcv_service.py` to use the new provider
3. No changes needed in API routes or frontend

## Indicator Calculation Pipeline

```
Raw OHLCV Data
     │
     ▼
Pandas DataFrame
     │
     ├──► close series → SMA(closes, 20)
     ├──► close series → RSI(closes, 14)
     └──► close series → MACD(closes, 12, 26, 9)
     │
     ▼
Return enriched JSON
```

## Error Handling Flow

```
Request → Validate → Fetch Data → Calculate → Return
                  │              │           │
                  ▼              ▼           ▼
              Invalid       API Failure   Calculation
              Symbol        Error         Error
                  │              │           │
                  ▼              ▼           ▼
              404 Response   503 Response  Error State
              + User Msg     + Retry       + Empty State
```
