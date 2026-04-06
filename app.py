from flask import Flask, render_template, request
import random
from datetime import datetime

app = Flask(__name__)

# ✅ FIXED symbols (no more TradingView errors)
STOCKS = [
    {"symbol": "AZN.L", "market": "UK", "chart_symbol": "AZN"},
    {"symbol": "BARC.L", "market": "UK", "chart_symbol": "BARC"},
    {"symbol": "BP.L", "market": "UK", "chart_symbol": "BP"},
    {"symbol": "HSBA.L", "market": "UK", "chart_symbol": "HSBC"},
    {"symbol": "SHEL.L", "market": "UK", "chart_symbol": "SHEL"},

    {"symbol": "AAPL", "market": "US", "chart_symbol": "NASDAQ:AAPL"},
    {"symbol": "MSFT", "market": "US", "chart_symbol": "NASDAQ:MSFT"},
    {"symbol": "NVDA", "market": "US", "chart_symbol": "NASDAQ:NVDA"},
    {"symbol": "TSLA", "market": "US", "chart_symbol": "NASDAQ:TSLA"},
]

def generate_signals():
    results = []
    for stock in STOCKS:
        results.append({
            "symbol": stock["symbol"],
            "market": stock["market"],
            "signal": random.choice(["BUY", "HOLD", "SELL"]),
            "confidence": round(random.uniform(50, 100), 1),
            "price": round(random.uniform(100, 2000), 2),
            "chart_symbol": stock["chart_symbol"],
        })
    results.sort(key=lambda x: x["confidence"], reverse=True)
    return results

@app.route("/")
def home():
    selected = request.args.get("symbol")
    scored = generate_signals()
    best = scored[0]

    if selected:
        for s in scored:
            if s["symbol"] == selected:
                best = s
                break

    return render_template("index.html", scored=scored, best=best, now=datetime.utcnow())

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
