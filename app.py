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

def safe_float(value):
    try:
        return round(float(value), 2)
    except Exception:
        return None

def get_period_high_low(df, days):
    sub = df.tail(days)
    if sub.empty:
        return None, None
    return safe_float(sub["High"].max()), safe_float(sub["Low"].min())

def get_stock_data(stock):
    try:
        df = yf.download(
            stock["symbol"],
            period="1y",
            interval="1d",
            auto_adjust=True,
            progress=False
        )

        if df is None or df.empty or len(df) < 30:
            return None

        latest = df.iloc[-1]
        price = float(latest["Close"])
        prev_price = float(df["Close"].iloc[-2])
        daily_move = ((price - prev_price) / prev_price) * 100 if prev_price else 0

        close = df["Close"]
        rsi = float(calc_rsi(close).iloc[-1])
        ma10 = float(close.rolling(10).mean().iloc[-1])
        ma20 = float(close.rolling(20).mean().iloc[-1])

        if price > ma10 > ma20:
            trend = "Strong Up"
        elif price > ma20:
            trend = "Up"
        elif price < ma10 < ma20:
            trend = "Strong Down"
        else:
            trend = "Down"

        score = 50.0
        score += 15 if trend == "Strong Up" else 8 if trend == "Up" else -15 if trend == "Strong Down" else -8
        score += 15 if rsi < 30 else 8 if rsi < 40 else -15 if rsi > 70 else -8 if rsi > 60 else 0
        score += min(daily_move * 3, 10) if daily_move > 0 else -min(abs(daily_move) * 3, 10)

        confidence = max(1, min(round(score, 1), 99.9))

        if confidence >= 65:
            signal = "BUY"
        elif confidence <= 35:
            signal = "SELL"
        else:
            signal = "HOLD"

        daily_high = safe_float(latest["High"])
        daily_low = safe_float(latest["Low"])

        weekly_high, weekly_low = get_period_high_low(df, 5)
        monthly_high, monthly_low = get_period_high_low(df, 21)
        high_3m, low_3m = get_period_high_low(df, 63)
        high_6m, low_6m = get_period_high_low(df, 126)
        high_9m, low_9m = get_period_high_low(df, 189)
        high_12m, low_12m = get_period_high_low(df, 252)

        return {
            "symbol": stock["symbol"],
            "market": stock["market"],
            "chart_symbol": stock["chart_symbol"],
            "signal": signal,
            "confidence": confidence,
            "price": round(price, 2),
            "daily_move": round(daily_move, 2),
            "rsi": round(rsi, 1),
            "trend": trend,

            "daily_high": daily_high,
            "daily_low": daily_low,
            "weekly_high": weekly_high,
            "weekly_low": weekly_low,
            "monthly_high": monthly_high,
            "monthly_low": monthly_low,
            "high_3m": high_3m,
            "low_3m": low_3m,
            "high_6m": high_6m,
            "low_6m": low_6m,
            "high_9m": high_9m,
            "low_9m": low_9m,
            "high_12m": high_12m,
            "low_12m": low_12m,
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
        return "No market data available."

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
