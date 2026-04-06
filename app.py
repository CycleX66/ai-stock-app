from flask import Flask, render_template
import yfinance as yf
import pandas as pd
import numpy as np

app = Flask(__name__)

# Stock list (UK + US)
STOCKS = [
    {"symbol": "AZN.L", "market": "UK", "chart_symbol": "NASDAQ:AZN"},
    {"symbol": "BARC.L", "market": "UK", "chart_symbol": "NYSE:BCS"},
    {"symbol": "BP.L", "market": "UK", "chart_symbol": "NYSE:BP"},
    {"symbol": "HSBA.L", "market": "UK", "chart_symbol": "NYSE:HSBC"},
    {"symbol": "SHEL.L", "market": "UK", "chart_symbol": "NYSE:SHEL"},

    {"symbol": "AAPL", "market": "US", "chart_symbol": "NASDAQ:AAPL"},
    {"symbol": "MSFT", "market": "US", "chart_symbol": "NASDAQ:MSFT"},
    {"symbol": "NVDA", "market": "US", "chart_symbol": "NASDAQ:NVDA"},
    {"symbol": "TSLA", "market": "US", "chart_symbol": "NASDAQ:TSLA"},
]


def calculate_rsi(data, period=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


def get_stock_data(stock):
    df = yf.download(stock["symbol"], period="3mo", interval="1d")

    if df.empty:
        return None

    df["RSI"] = calculate_rsi(df["Close"])
    df["MA20"] = df["Close"].rolling(window=20).mean()

    latest = df.iloc[-1]

    # Signal logic
    if latest["RSI"] < 30:
        signal = "BUY"
    elif latest["RSI"] > 70:
        signal = "SELL"
    else:
        signal = "HOLD"

    confidence = round(abs(50 - latest["RSI"]) * 2, 1)

    return {
        "symbol": stock["symbol"],
        "market": stock["market"],
        "price": round(latest["Close"], 2),
        "rsi": round(latest["RSI"], 1),
        "trend": "Up" if latest["Close"] > latest["MA20"] else "Down",
        "signal": signal,
        "confidence": confidence,
        "chart_symbol": stock["chart_symbol"]
    }


@app.route("/")
def index():
    results = []

    for stock in STOCKS:
        data = get_stock_data(stock)
        if data:
            results.append(data)

    # Sort by confidence
    results = sorted(results, key=lambda x: x["confidence"], reverse=True)

    best = results[0] if results else None

    return render_template("index.html", scored=results, best=best)


if __name__ == "__main__":
    app.run(debug=True)
