from flask import Flask, render_template
import random
from datetime import datetime

app = Flask(__name__)

STOCKS = [
    {"symbol": "AZN.L", "market": "UK", "chart_symbol": "LSE:AZN"},
    {"symbol": "BARC.L", "market": "UK", "chart_symbol": "LSE:BARC"},
    {"symbol": "BP.L", "market": "UK", "chart_symbol": "LSE:BP"},
    {"symbol": "HSBA.L", "market": "UK", "chart_symbol": "LSE:HSBA"},
    {"symbol": "SHEL.L", "market": "UK", "chart_symbol": "LSE:SHEL"},
    {"symbol": "AAPL", "market": "US", "chart_symbol": "NASDAQ:AAPL"},
    {"symbol": "MSFT", "market": "US", "chart_symbol": "NASDAQ:MSFT"},
    {"symbol": "NVDA", "market": "US", "chart_symbol": "NASDAQ:NVDA"},
    {"symbol": "TSLA", "market": "US", "chart_symbol": "NASDAQ:TSLA"},
]

def generate_signals():
    results = []
    for stock in STOCKS:
        signal = random.choice(["BUY", "HOLD", "SELL"])
        confidence = round(random.uniform(50, 100), 1)
        results.append({
            "symbol": stock["symbol"],
            "market": stock["market"],
            "signal": signal,
            "confidence": confidence,
            "price": round(random.uniform(100, 2000), 2),
            "daily_move": round(random.uniform(-3, 3), 2),
            "rsi": round(random.uniform(30, 75), 1),
            "trend": random.choice(["Up", "Down"]),
            "chart_symbol": stock["chart_symbol"],
        })
    results.sort(key=lambda x: x["confidence"], reverse=True)
    return results

@app.route("/")
def home():
    scored = generate_signals()
    best = scored[0]
    return render_template(
        "index.html",
        scored=scored,
        best=best,
        now=datetime.utcnow()
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
