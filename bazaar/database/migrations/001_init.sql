-- Bazaar PSX Terminal - Initial Database Migration

CREATE TABLE IF NOT EXISTS ohlcv_data (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    symbol VARCHAR(10) NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    open DOUBLE PRECISION NOT NULL,
    high DOUBLE PRECISION NOT NULL,
    low DOUBLE PRECISION NOT NULL,
    close DOUBLE PRECISION NOT NULL,
    volume DOUBLE PRECISION NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_ohlcv_symbol ON ohlcv_data (symbol);
CREATE INDEX IF NOT EXISTS ix_ohlcv_timeframe ON ohlcv_data (timeframe);
CREATE INDEX IF NOT EXISTS ix_ohlcv_timestamp ON ohlcv_data (timestamp);
CREATE INDEX IF NOT EXISTS ix_ohlcv_symbol_timeframe ON ohlcv_data (symbol, timeframe);

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS api_config (
    id SERIAL PRIMARY KEY,
    api_name VARCHAR(100) NOT NULL,
    api_key TEXT,
    api_url VARCHAR(255),
    environment VARCHAR(20) DEFAULT 'production',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS watchlists (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    symbol VARCHAR(10) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS alerts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    symbol VARCHAR(10) NOT NULL,
    condition VARCHAR(50) NOT NULL,
    threshold DOUBLE PRECISION NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
