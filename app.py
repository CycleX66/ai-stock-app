from flask import Flask, render_template, request
import yfinance as yf
import pandas as pd
import time
from datetime import datetime, timezone

app = Flask(__name__)

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

def calc_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss.replace(0, pd.NA)
    return (100 - (100 / (1 + rs))).fillna(50)

def safe_float(v):
    try:
        return round(float(v), 2)
    except:
        return None

def get_data_with_retry(symbol):
    for _ in range(3):  # try 3 times
        df = yf.download(symbol, period="1y", interval="1d", progress=False)
        if df is not None and not df.empty:
            return df
        time.sleep(1)
    return None

def get_stock(stock):
    df = get_data_with_retry(stock["symbol"])
    if df is None or df.empty:
        return None

    close = df["Close"]

    price = float(close.iloc[-1])
    prev = float(close.iloc[-2]) if len(close) > 1 else price
    move = ((price - prev) / prev) * 100 if prev else 0

    rsi = float(calc_rsi(close).iloc[-1])

    ma10 = float(close.rolling(10).mean().iloc[-1])
    ma20 = float(close.rolling(20).mean().iloc[-1])

    trend = "Up" if price > ma20 else "Down"

    score = 50
    score += 10 if trend == "Up" else -10
    score += 10 if rsi < 40 else -10 if rsi > 60 else 0

    confidence = max(1, min(score, 99))

    signal = "BUY" if confidence > 65 else "SELL" if confidence < 35 else "HOLD"

    return {
        "symbol": stock["symbol"],
        "chart_symbol": stock["chart_symbol"],
        "price": round(price, 2),
        "signal": signal,
        "confidence": confidence,
        "daily_high": safe_float(df["High"].iloc[-1]),
        "daily_low": safe_float(df["Low"].iloc[-1]),
    }

def generate():
    data = []
    for s in STOCKS:
        d = get_stock(s)
        if d:
            data.append(d)
    return sorted(data, key=lambda x: x["confidence"], reverse=True)

@app.route("/")
def home():
    scored = generate()

    # 🔥 fallback if API fails
    if not scored:
        scored = [
            {"symbol": "AAPL", "chart_symbol": "NASDAQ:AAPL", "price": 180, "signal": "HOLD", "confidence": 50, "daily_high": 182, "daily_low": 178}
        ]

    best = scored[0]

    selected = request.args.get("symbol")
    if selected:
        for s in scored:
            if s["symbol"] == selected:
                best = s

    return render_template("index.html", scored=scored, best=best, now=datetime.now(timezone.utc))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
