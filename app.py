from flask import Flask, render_template, request
import yfinance as yf
import pandas as pd
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
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50)

def get_stock_data(stock):
    try:
        df = yf.download(
            stock["symbol"],
            period="6mo",
            interval="1d",
            auto_adjust=True,
            progress=False
        )

        if df is None or df.empty or len(df) < 30:
            return None

        close = df["Close"].squeeze()

        latest_price = float(close.iloc[-1])
        prev_price = float(close.iloc[-2])
        daily_move = ((latest_price - prev_price) / prev_price) * 100 if prev_price else 0

        rsi = float(calc_rsi(close).iloc[-1])
        ma10 = float(close.rolling(10).mean().iloc[-1])
        ma20 = float(close.rolling(20).mean().iloc[-1])

        if latest_price > ma10 > ma20:
            trend = "Strong Up"
        elif latest_price > ma20:
            trend = "Up"
        elif latest_price < ma10 < ma20:
            trend = "Strong Down"
        else:
            trend = "Down"

        score = 50.0

        if trend == "Strong Up":
            score += 20
        elif trend == "Up":
            score += 10
        elif trend == "Strong Down":
            score -= 20
        elif trend == "Down":
            score -= 10

        if rsi < 30:
            score += 20
        elif rsi < 40:
            score += 10
        elif rsi > 70:
            score -= 20
        elif rsi > 60:
            score -= 10

        if daily_move > 0:
            score += min(daily_move * 3, 10)
        else:
            score -= min(abs(daily_move) * 3, 10)

        confidence = max(1, min(round(score, 1), 99.9))

        if confidence >= 65:
            signal = "BUY"
        elif confidence <= 35:
            signal = "SELL"
        else:
            signal = "HOLD"

        return {
            "symbol": stock["symbol"],
            "market": stock["market"],
            "chart_symbol": stock["chart_symbol"],
            "signal": signal,
            "confidence": confidence,
            "price": round(latest_price, 2),
            "daily_move": round(daily_move, 2),
            "rsi": round(rsi, 1),
            "trend": trend,
        }

    except Exception:
        return None

def generate_signals():
    results = []
    for stock in STOCKS:
        data = get_stock_data(stock)
        if data:
            results.append(data)
    results.sort(key=lambda x: x["confidence"], reverse=True)
    return results

@app.route("/")
def home():
    selected_symbol = request.args.get("symbol")
    scored = generate_signals()

    if not scored:
        return "No market data available right now."

    best = scored[0]

    if selected_symbol:
        for stock in scored:
            if stock["symbol"] == selected_symbol:
                best = stock
                break

    return render_template(
        "index.html",
        scored=scored,
        best=best,
        now=datetime.now(timezone.utc)
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
