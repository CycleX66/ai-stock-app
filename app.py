from flask import Flask, render_template, request
import yfinance as yf
import pandas as pd
from datetime import datetime, timezone

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
        df = yf.download(stock["symbol"], period="3mo", interval="1d", auto_adjust=True, progress=False)

        if df is None or df.empty or len(df) < 20:
            return None

        close = df["Close"].squeeze()
        price = float(close.iloc[-1])
        prev = float(close.iloc[-2])
        move = ((price - prev) / prev) * 100

        rsi = float(calc_rsi(close).iloc[-1])
        ma10 = float(close.rolling(10).mean().iloc[-1])
        ma20 = float(close.rolling(20).mean().iloc[-1])

        if price > ma10 > ma20:
            trend = "Up"
        elif price < ma10 < ma20:
            trend = "Down"
        else:
            trend = "Sideways"

        score = 50

        if trend == "Up":
            score += 20
        elif trend == "Down":
            score -= 20

        if rsi < 35:
            score += 10
        elif rsi > 70:
            score -= 10

        if move > 0:
            score += min(abs(move) * 4, 15)
        else:
            score -= min(abs(move) * 4, 15)

        confidence = max(1, min(round(score, 1), 99.9))

        if confidence >= 60:
            signal = "BUY"
        elif confidence <= 40:
            signal = "SELL"
        else:
            signal = "HOLD"

        return {
            "symbol": stock["symbol"],
            "chart_symbol": stock["chart_symbol"],
            "signal": signal,
            "confidence": confidence,
            "price": round(price, 2),
        }

    except:
        return None

def generate():
    results = []
    for s in STOCKS:
        data = get_stock_data(s)
        if data:
            results.append(data)

    results.sort(key=lambda x: x["confidence"], reverse=True)
    return results

@app.route("/")
def home():
    selected = request.args.get("symbol")
    scored = generate()

    best = scored[0]

    if selected:
        for s in scored:
            if s["symbol"] == selected:
                best = s

    return render_template(
        "index.html",
        scored=scored,
        best=best,
        now=datetime.now(timezone.utc)
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
