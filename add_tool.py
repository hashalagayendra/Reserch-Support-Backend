import sys
import os

# Add the project root to the sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.session import SessionLocal
from app.db.models import AITool

def add_tool():
    db = SessionLocal()
    try:
        new_tool = AITool(
            project_id=1,
            tool_title="getBitcoinPrice",
            description="Fetch current Bitcoin price and details from CoinGecko free public API (no key required)",
            argument={"currency": {"type": "string", "description": "The fiat currency to display price in, e.g. usd, eur, gbp, jpy, etc."}},
            api_url="https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies={currency}",
            http_method="GET",
            headers={"Accept": "application/json"}
        )
        db.add(new_tool)
        db.commit()
        print("Tool 'getBitcoinPrice' added successfully!")
    except Exception as e:
        print(f"Error adding tool: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    add_tool()
