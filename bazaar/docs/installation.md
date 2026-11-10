# Installation Guide

## Prerequisites

- **Node.js** 18+ (https://nodejs.org)
- **Python** 3.10+ (https://python.org)
- **PostgreSQL** 14+ (https://postgresql.org)
- **Git** (https://git-scm.com)

## Step 1: Clone Repository

```bash
cd ~/Desktop/trading
git clone <repository-url> bazaar
cd bazaar
```

## Step 2: Setup Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate    # Windows

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
# Edit .env with your credentials

# Setup database
psql -U postgres -c "CREATE DATABASE bazaar;"
```

### Configure `.env`

```bash
DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/bazaar
PSX_API_KEY=your_psx_api_key
PSX_API_URL=https://api.psx.com/v1
PSX_API_SECRET=your_psx_api_secret
SECRET_KEY=change-this-to-a-strong-random-key
```

## Step 3: Setup Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend runs at `http://localhost:3000`

## Step 4: Start Backend

```bash
cd backend

# Start the server
python -m app.main
```

Backend runs at `http://localhost:8000`

## Step 5: Verify Installation

Open browser to `http://localhost:3000` — the Bazaar terminal should load.

Test the API:
```bash
curl http://localhost:8000/api/market/health
curl http://localhost:8000/api/market/symbols
curl http://localhost:8000/api/market/ohlcv/OGDC
```

## Running Tests

```bash
# Backend tests
cd backend
python -m pytest app/tests/ -v

# Frontend tests (when added)
cd frontend
npm test
```

## Building for Production

```bash
# Frontend
cd frontend
npm run build

# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Docker (Optional)

```bash
# Build all services
docker-compose up --build
```
