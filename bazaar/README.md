# Bazaar — PSX Terminal

A professional stock technical-analysis application designed for the Pakistan Stock Exchange (PSX).

## Architecture

```
bazaar/
├── frontend/          # React + TypeScript + Tailwind CSS
│   ├── src/
│   │   ├── components/    # React components (TopBar, Watchlist, Chart, SignalsPanel)
│   │   ├── pages/         # Page-level views
│   │   ├── hooks/         # Custom React hooks
│   │   ├── utils/         # Indicator calculations, formatters
│   │   ├── services/      # API service layer
│   │   ├── store/         # Zustand state management
│   │   ├── types/         # TypeScript type definitions
│   │   └── styles/        # Global styles, Tailwind config
│   └── public/            # Static assets
├── backend/           # Python + FastAPI
│   └── app/
│       ├── api/         # Route handlers (market data, config)
│       ├── core/        # Config, security, database
│       ├── models/      # SQLAlchemy ORM models
│       ├── schemas/     # Pydantic schemas
│       ├── services/    # Business logic
│       ├── data/        # Data fetching & processing
│       └── tests/       # Unit tests
├── database/          # PostgreSQL migrations
├── docs/              # Documentation
└── charts/            # Chart component library
```

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, TypeScript 5, Tailwind CSS 3 |
| State | Zustand |
| Charts | SVG (TradingView Lightweight Charts planned) |
| Backend | Python 3.10+, FastAPI |
| Data | Pandas, NumPy |
| Database | PostgreSQL + SQLAlchemy 2.0 |
| Auth | JWT, Passlib (bcrypt) |
| Build | Vite |

## Getting Started

### Prerequisites
- Node.js 18+
- Python 3.10+
- PostgreSQL 14+

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
The app runs at `http://localhost:3000`.

### Backend Setup
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env  # Edit with your credentials
python -m app.main
```
The API runs at `http://localhost:8000`.

### Database Setup
```bash
createdb bazaar
# Or use PostgreSQL tools to create the database
```

## API Endpoints

### Market Data (`/api/market`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/market/health` | Service health + which SDKs are live |
| GET | `/api/market/symbols` | Tradable symbol universe |
| GET | `/api/market/market-watch` | Full PSX market watch (`?limit=100`) |
| GET | `/api/market/quote/{symbol}` | Fast price snapshot for one symbol |
| GET | `/api/market/ohlcv/{symbol}` | OHLCV bars + SMA/RSI/MACD (`?timeframe=1M\|3M\|6M\|1Y`) |
| GET | `/api/market/ohlcv/{symbol}/summary` | Last price, trend, support/resistance |

### Trading (`/api/trading`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/trading/status` | Connection + paper/live mode |
| GET | `/api/trading/account` | Equity, cash, buying power |
| GET | `/api/trading/portfolio` | Mark-to-market valuation |
| GET | `/api/trading/positions` | Open positions |
| GET | `/api/trading/orders` | Order history (`?status=pending`) |
| POST | `/api/trading/orders` | Submit an order |
| DELETE | `/api/trading/orders/{order_id}` | Cancel a pending order |

### Prediction (`/api/predict`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/predict/{symbol}` | Next-session up/down forecast (`?timeframe=3M\|6M\|1Y`) |

A small RandomForest is trained fresh on each request, on engineered
features (1-day and 5-day returns, SMA-20 gap, RSI-14, MACD histogram,
volume change) built from the same OHLCV history the chart uses. It reports
a direction (`up`/`down`), a confidence score, and a holdout accuracy from
its own train/test split — an educational, explainable model, not financial
advice.

### Configuration (`/api/config`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/config/` | Non-secret config summary |
| GET | `/api/config/env-check` | Which required env vars are missing |

Interactive docs are served at `http://localhost:8000/docs`.

## Data Sources

Two SDKs back the data layer, and they're not equally required:

- **`pypsx-toolkit`** — **free**, public PSX market data (market watch,
  quotes, historical OHLCV, fundamentals). No account, no API key. This is
  what powers the chart, watchlist, and prediction endpoint.
- **`pypsx`** — **authenticated** `TradingClient`. Only needed if you want
  the `/api/trading` endpoints to place real orders against an account.
  Market data and predictions work fully without it.

Every endpoint falls back to generated mock data when a live call is
unavailable or fails, so the UI never breaks. The `source` field in each
response tells you which path served the data: `"pypsx"` or `"mock"`.

Set `USE_PYPSX=False` in `.env` to force mock data everywhere.

## Modules Roadmap

### Phase 1: Foundation
- [x] Market Data Module
- [x] Chart Module (Price, Volume, RSI, MACD)
- [x] UI Dashboard (from demo.html)
- [x] Watchlist with sparklines
- [x] Timeframe Selection (1M, 3M, 6M, 1Y)

### Phase 2: Indicators & Signals
- [ ] Indicator Module (SMA, EMA, RSI, MACD, Bollinger Bands)
- [ ] Signal Module (Trend, Momentum, Key Levels)
- [ ] Settings Module (API configuration)

### Phase 3: Strategy & Analysis
- [ ] Strategy Module
- [ ] AI Analysis Module
- [ ] Signal Module
- [ ] Backtesting Module
- [ ] Risk Management Module

### Phase 4: Advanced
- [ ] WebSocket real-time data
- [ ] Paper trading simulator
- [ ] Alert system
- [ ] Drawing tools on charts
- [ ] Portfolio tracker
- [ ] News/sentiment feed
- [ ] Custom indicator builder

## Project Structure - Data Flow

```
Frontend (React) → WebSocket/HTTP → Backend (FastAPI) → Data Service → PSX API
     ↓                                                        ↓
  State (Zustand)                                      PostgreSQL
     ↓
  UI Components → Chart SVG, Signals Panel, Watchlist
```

## Key Principles

1. **Never hardcode API keys** - Use environment variables
2. **Modular architecture** - Each module is independent and extensible
3. **Normalized OHLCV model** - `timestamp, open, high, low, close, volume, symbol`
4. **Error handling** - Invalid symbols, API failures, rate limits
5. **Loading & empty states** - All data views have states
6. **Logging** - Comprehensive logging at all layers
7. **Unit tests** - Test coverage for all critical functions

## Credentials

**Market data and predictions need no credentials at all** — `pypsx-toolkit`
is free and keyless, and `USE_PYPSX=True` in `.env.example` is already the
default. Run the app as-is and the chart, watchlist, and `/api/predict` all
use live PSX data out of the box.

An API key is only needed if you also want to place orders through
`/api/trading`:

1. Create an account at https://markets.pypsx.com and generate an API key
   (Dashboard > Settings > API Keys). Paper keys start with `PK_`.
2. In `backend/.env`, fill in:

```
PYPSX_API_KEY_ID=PK_your_key_id
PYPSX_API_SECRET_KEY=your_secret
PYPSX_PAPER=True
```

3. The secret is shown only once at creation. If it leaks, revoke the key in
   the dashboard and generate a new one.

`.env` is gitignored. Never commit it, and never paste keys into source files,
screenshots, or submitted reports.

### Live trading safety gate

Order submission is blocked unless one of these holds:
- `PYPSX_PAPER=True` (paper money, the default), or
- `ALLOW_LIVE_TRADING=True` (explicit opt-in for real money).

Leave both at their defaults while developing.

## License

MIT
