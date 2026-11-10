import sys
import os

# Add the backend directory to path so 'app' package is importable
sys.path.insert(0, os.path.dirname(__file__))

# Set environment to avoid PyPSX trading client connection
os.environ['PYPSX_PAPER'] = 'true'
os.environ['PYPSX_API_KEY_ID'] = ''
os.environ['PYPSX_API_SECRET_KEY'] = ''
os.environ['PYPSX_API_TOKEN'] = ''

# Now import the app
from app.main import app

print("App imported successfully")
print("Routes:", [getattr(r, "path", str(r)) for r in app.routes])

# Test the analysis endpoint can be called
from fastapi.testclient import TestClient
client = TestClient(app)

# Test root endpoint
response = client.get("/")
print("\nRoot endpoint:", response.status_code, response.json())

# Test health endpoint
response = client.get("/api/market/health")
print("Health endpoint:", response.status_code, response.json())

# Test analysis endpoint (with mock data - should fall back to mock since no live data)
response = client.get("/api/analysis/OGDC?timeframe=3M")
print("Analysis endpoint:", response.status_code)
if response.status_code == 200:
    data = response.json()
    print("  Symbol:", data.get("symbol") if isinstance(data, dict) else "N/A")
    print("  Signal:", data.get("signal") if isinstance(data, dict) else "N/A")
    print("  Bullish score:", data.get("bullish_score") if isinstance(data, dict) else "N/A")
    print("  Bearish score:", data.get("bearish_score") if isinstance(data, dict) else "N/A")
    print("  Neutral score:", data.get("neutral_score") if isinstance(data, dict) else "N/A")
    print("  Trade levels entry:", data.get("trade_levels", {}).get("entry_zone") if isinstance(data.get("trade_levels"), dict) else "N/A")
else:
    print("  Error:", response.json() if hasattr(response, 'json') else "N/A")