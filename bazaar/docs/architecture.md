# Project Architecture

## Overview

Bazaar is a client-server application built for PSX (Pakistan Stock Exchange) technical analysis.

## System Diagram

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Frontend      │     │   Backend       │     │   Database      │
│   (React)       │◄───►│   (FastAPI)     │◄───►│   (PostgreSQL)  │
│   Port 3000     │     │   Port 8000     │     │   Port 5432     │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                       │
        ▼                       ▼
  ┌───────────┐         ┌───────────┐
  │  Browser  │         │  PSX API  │
  │           │         │  (External)│
  └───────────┘         └───────────┘
```

## Frontend Architecture (React)

### Component Hierarchy
```
App
├── AppLayout (CSS Grid)
│   ├── TopBar (Brand, Search, Clock, Index Widget)
│   ├── TickerStrip (Scrolling price ticker)
│   ├── Watchlist (Symbol rows with sparklines)
│   ├── Chart (Multi-pane OHLCV visualization)
│   │   ├── PricePane (Candlesticks + SMA20)
│   │   ├── VolumePane (Volume bars)
│   │   ├── RSIPane (RSI 14)
│   │   └── MACDPane (MACD histogram)
│   └── SignalsPanel (Trend, Momentum, Key Levels, Read)
```

### State Management (Zustand)
```typescript
interface Store {
  symbol: string;
  tf: string;
  setSymbol: (symbol: string) => void;
  setTimeframe: (tf: string) => void;
}
```

### Data Flow
```
User Interaction → Zustand Store → Component Re-render → API Call → Backend
Backend Response → Update Store → Component Re-render → UI Update
```

## Backend Architecture (FastAPI)

### Layer Structure
```
API Routes (FastAPI Routers)
    │
    ├── /api/market    → Market Data endpoints
    ├── /api/config    → Configuration endpoints
    │
    ▼
Services (Business Logic)
    │
    ▼
Data Layer (Data Fetching & Processing)
    │
    ▼
Database (PostgreSQL via SQLAlchemy 2.0)
```

### Key Files
- `app/main.py` — Application entry point, lifespan management
- `app/core/config.py` — Environment-based configuration
- `app/core/database.py` — Async database engine & session management
- `app/core/security.py` — JWT authentication, password hashing
- `app/api/market_data.py` — Market data endpoints
- `app/data/ohlcv_service.py` — Data generation and indicator calculations

## Module Roadmap

### Phase 1: Foundation (Completed)
- Market Data Module
- Chart Module (Price, Volume, RSI, MACD)
- UI Dashboard

### Phase 2: Indicators & Signals
- Indicator Module
- Signal Module
- Settings Module

### Phase 3: Strategy & Analysis
- Strategy Module
- AI Analysis Module
- Backtesting Module
- Risk Management Module

### Phase 4: Advanced Features
- WebSocket real-time data
- Paper trading
- Drawing tools
- Portfolio tracker

## Error Handling Strategy

| Error Type | Frontend | Backend |
|------------|----------|---------|
| Invalid Symbol | Show empty state + message | 404 with detail |
| API Failure | Retry mechanism + error toast | Circuit breaker |
| Missing Data | Empty chart + message | Empty response |
| Rate Limit | Show warning | 429 with Retry-After |

## Security Model
- JWT-based authentication
- API keys stored in environment variables only
- CORS configured for frontend origin
- Input validation via Pydantic schemas
- Password hashing with bcrypt
