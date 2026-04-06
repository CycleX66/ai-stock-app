from flask import Flask, render_template, request
import yfinance as yf
from datetime import datetime

app = Flask(__name__)

STOCKS = [
    {"symbol": "AAPL", "chart_symbol": "NASDAQ:AAPL"},
    {"symbol": "MSFT", "chart_symbol": "NASDAQ:MSFT"},
    {"symbol": "NVDA", "chart_symbol": "NASDAQ:NVDA"},
    {"symbol": "TSLA", "chart_symbol": "NASDAQ:TSLA"},
]

def get_stock(symbol, chart_symbol):
    try:
        df = yf.download(symbol, period="1mo", interval="1d", progress=False, auto_adjust=True)
        if df is None or df.empty:
            return None

        close = df["Close"].squeeze()
        high = df["High"].squeeze()
        low = df["Low"].squeeze()

        price = float(close.iloc[-1])
        daily_high = float(high.iloc[-1])
        daily_low = float(low.iloc[-1])

        return {
            "symbol": symbol,
            "chart_symbol": chart_symbol,
            "price": round(price, 2),
            "signal": "HOLD",
            "confidence": 50.0,
            "daily_high": round(daily_high, 2),
            "daily_low": round(daily_low, 2),
        }
    except Exception:
        return None

@app.route("/")
def home():
    scored = []

    for stock in STOCKS:
        item = get_stock(stock["symbol"], stock["chart_symbol"])
        if item:
            scored.append(item)

    if not scored:
        scored = [{
            "symbol": "AAPL",
            "chart_symbol": "NASDAQ:AAPL",
            "price": 180.00,
            "signal": "HOLD",
            "confidence": 50.0,
            "daily_high": 182.00,
            "daily_low": 178.00,
        }]

    best = scored[0]

    selected = request.args.get("symbol")
    if selected:
        for item in scored:
            if item["symbol"] == selected:
                best = item
                break

    return render_template(
        "index.html",
        scored=scored,
        best=best,
        now=datetime.now()
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
