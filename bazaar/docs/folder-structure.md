# Folder Structure

```
bazaar/
├── frontend/                          # React + TypeScript + Tailwind CSS
│   ├── public/                        # Static assets
│   │   └── vite.svg
│   └── src/
│       ├── components/                # React components
│       │   ├── AppLayout.tsx          # Main grid layout
│       │   ├── TopBar.tsx             # Header with search, clock, index
│       │   ├── TickerStrip.tsx        # Scrolling price ticker
│       │   ├── Watchlist.tsx          # Symbol list with sparklines
│       │   ├── SignalsPanel.tsx       # Trend, momentum, key levels
│       │   ├── chart/                 # Chart components
│       │   │   └── Chart.tsx          # Multi-pane chart (price, vol, rsi, macd)
│       │   └── ui/                    # Reusable UI components
│       ├── pages/                     # Page-level views
│       ├── hooks/                     # Custom React hooks
│       ├── utils/                     # Indicator calculations, formatters
│       │   └── indicators.ts          # SMA, EMA, RSI, MACD, sparkPath, fmt
│       ├── services/                  # API service layer
│       ├── store/                     # Zustand state management
│       │   └── useStore.ts            # Global app state
│       ├── types/                     # TypeScript type definitions
│       │   └── index.ts               # OHLCV, Symbol, AppState interfaces
│       ├── data/                      # Data definitions
│       │   └── symbols.ts             # PSX symbols and generated series
│       ├── styles/                    # Global styles
│       │   └── index.css              # Tailwind + CSS variables + grid layout
│       ├── App.tsx                    # Root component
│       └── main.tsx                   # Entry point
│   ├── index.html                     # HTML template
│   ├── vite.config.ts                 # Vite configuration
│   ├── tsconfig.json                  # TypeScript config
│   ├── tsconfig.node.json             # TypeScript node config
│   ├── tailwind.config.js             # Tailwind CSS config
│   ├── postcss.config.js              # PostCSS config
│   └── package.json                   # Dependencies
├── backend/                           # Python + FastAPI
│   └── app/
│       ├── main.py                    # Application entry point
│       ├── api/                       # Route handlers
│       │   ├── __init__.py
│       │   ├── market_data.py         # Market data endpoints
│       │   └── config.py              # Configuration endpoints
│       ├── core/                      # Core infrastructure
│       │   ├── __init__.py
│       │   ├── config.py              # Environment-based settings
│       │   ├── security.py            # JWT, password hashing
│       │   └── database.py            # Async SQLAlchemy engine
│       ├── models/                    # SQLAlchemy ORM models
│       │   ├── __init__.py
│       │   ├── ohlcv.py               # OHLCV data model
│       │   └── user.py                # User model
│       ├── schemas/                   # Pydantic validation schemas
│       │   ├── __init__.py
│       │   ├── ohlcv.py               # OHLCV schemas
│       │   ├── user.py                # User schemas
│       │   └── config.py              # Config schemas
│       ├── services/                  # Business logic services
│       │   └── __init__.py
│       ├── data/                      # Data fetching & processing
│       │   ├── __init__.py
│       │   └── ohlcv_service.py       # Data generation, indicators
│       └── tests/                     # Unit tests
│           └── test_main.py
│   ├── requirements.txt               # Python dependencies
│   └── pyproject.toml                 # Project metadata
├── database/                          # Database files
│   └── migrations/
│       └── 001_init.sql               # Initial schema
├── docs/                              # Documentation
│   ├── architecture.md                # System architecture
│   ├── installation.md                # Setup guide
│   ├── how-it-works.md                # Data flow explanation
│   └── folder-structure.md            # Detailed file structure
├── charts/                            # Chart component library
├── .env.example                       # Environment template
└── README.md                          # Project overview
```
