from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data

def test_health():
    response = client.get("/api/market/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"

def test_symbols():
    response = client.get("/api/market/symbols")
    assert response.status_code == 200
    data = response.json()
    assert "symbols" in data

def test_get_ohlcv():
    response = client.get("/api/market/ohlcv/OGDC")
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "OGDC"
    assert len(data["data"]) > 0

def test_invalid_symbol():
    response = client.get("/api/market/ohlcv/INVALID")
    assert response.status_code == 404

def test_summary():
    response = client.get("/api/market/ohlcv/OGDC/summary")
    assert response.status_code == 200
    data = response.json()
    assert "last_price" in data

def test_config_env_check():
    response = client.get("/api/config/env-check")
    assert response.status_code == 200
    data = response.json()
    assert "has_keys" in data
