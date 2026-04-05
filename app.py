from flask import Flask, render_template
import random
from datetime import datetime, timezone

app = Flask(__name__)

# Simple stock list
STOCKS = [
    {"symbol": "AZN.L", "market": "UK"},
    {"symbol": "BARC.L", "market": "UK"},
    {"symbol": "BP.L", "market": "UK"},
    {"symbol": "HSBA.L", "market": "UK"},
    {"symbol": "SHEL.L", "market": "UK"},
    {"symbol": "AAPL", "market": "US"},
    {"symbol": "MSFT", "market": "US"},
    {"symbol": "NVDA", "market": "US"},
    {"symbol": "TSLA", "market": "US"},
]

def market_status():
    now = datetime.now(timezone.utc)
    return {
        "uk": "OPEN" if 8 <= now.hour <= 16 else "CLOSED",
        "us": "OPEN" if 14 <= now.hour <= 21 else "CLOSED"
    }

def generate_signals():
    results = []
    for stock in STOCKS:
        confidence = round(random.uniform(40, 100), 1)
        if confidence > 60:
            signal = "BUY"
        elif confidence < 45:
            signal = "SELL"
        else:
            signal = "HOLD"

        results.append({
            "symbol": stock["symbol"],
            "market": stock["market"],
            "signal": signal,
            "confidence": confidence,
            "price": round(random.uniform(100, 2000), 2),
            "daily_move": round(random.uniform(-3, 3), 2)
        })
    return sorted(results, key=lambda x: x["confidence"], reverse=True)

@app.route("/")
def index():
    scored = generate_signals()
    best = scored[0] if scored else None

    return render_template(
        "index.html",
        scored=scored,
        best=best,
        statuses=market_status(),   # ✅ FIXES YOUR ERROR
        paper_value=100000,
        cash=84684,
        positions={},
        history=[],
        last_run=str(datetime.now(timezone.utc)),
        auto_picks=scored[:5],
        settings={"markets": "both", "safe_mode": True},
        custom_set=set()
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
