from flask import Flask, render_template, request, redirect, url_for
import yfinance as yf
import pandas as pd
from datetime import datetime, timezone

app = Flask(__name__)

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

def calc_rsi(series, period=14):
    delta = series.diff()https://ai-stock-app-a74r.onrender.com/
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / avg_loss.replace(0, pd.NA)
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50)

def get_stock_data(symbol):
    try:
        df = yf.download(symbol, period="3mo", interval="1d", auto_adjust=True, progress=False)

        if df is None or df.empty or len(df) < 20:
            return None

        close = df["Close"].squeeze()
        latest_price = float(close.iloc[-1])
        prev_price = float(close.iloc[-2]) if len(close) > 1 else latest_price
        daily_move = ((latest_price - prev_price) / prev_price) * 100 if prev_price else 0

        rsi_series = calc_rsi(close)
        rsi = float(rsi_series.iloc[-1])

        ma10 = float(close.rolling(10).mean().iloc[-1])
        ma20 = float(close.rolling(20).mean().iloc[-1])

        if latest_price > ma10 > ma20:
            trend = "Up"
        elif latest_price < ma10 < ma20:
            trend = "Down"
        else:
            trend = "Sideways"

        score = 50.0

        if trend == "Up":
            score += 18
        elif trend == "Down":
            score -= 18

        if rsi < 35:
            score += 12
        elif rsi > 70:
            score -= 12
        elif 45 <= rsi <= 60:
            score += 5

        if daily_move > 0:
            score += min(abs(daily_move) * 4, 15)
        else:
            score -= min(abs(daily_move) * 4, 15)

        confidence = max(1, min(round(score, 1), 99.9))

        if confidence >= 60:
            signal = "BUY"
        elif confidence <= 40:
            signal = "SELL"
        else:
            signal = "HOLD"

        return {
            "symbol": symbol,
            "price": round(latest_price, 2),
            "daily_move": round(daily_move, 2),
            "rsi": round(rsi, 1),
            "trend": trend,
            "confidence": confidence,
            "signal": signal,
        }

    except Exception:
        return None

def generate_signals():
    results = []

    for stock in STOCKS:
        data = get_stock_data(stock["symbol"])
        if data:
            data["market"] = stock["market"]
            results.append(data)

    results.sort(key=lambda x: x["confidence"], reverse=True)
    return results

@app.route("/")
def index():
    scored = generate_signals()
    best = scored[0] if scored else {
        "symbol": "N/A",
        "signal": "HOLD",
        "confidence": 0,
        "price": 0,
        "rsi": 0,
        "trend": "N/A"
    }

    return render_template(
        "index.html",
        scored=scored,
        best=best,
        statuses=market_status(),
        paper_value=100000,
        cash=84684,
        positions={},
        history=[],
        last_run=str(datetime.now(timezone.utc)),
        auto_picks=scored[:5],
        settings={"markets": "UK + US", "safe_mode": True},
        custom_set=set()
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
