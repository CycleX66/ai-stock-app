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

def get_signal(df):
    df["MA20"] = df["Close"].rolling(20).mean()
    df["MA50"] = df["Close"].rolling(50).mean()

    last = df.iloc[-1]

    if last["MA20"] > last["MA50"]:
        return "BUY", 75
    elif last["MA20"] < last["MA50"]:
        return "SELL", 75
    else:
        return "HOLD", 50

def get_range(df, days):
    sub = df.tail(days)
    return round(sub["High"].max(), 2), round(sub["Low"].min(), 2)

def get_stock(symbol, chart_symbol):
    try:
        df = yf.Ticker(symbol).history(period="1y")

        if df.empty:
            return None

        df = df.dropna()

        price = round(df["Close"].iloc[-1], 2)

        signal, confidence = get_signal(df)

        d_high = round(df["High"].iloc[-1], 2)
        d_low = round(df["Low"].iloc[-1], 2)

        w_high, w_low = get_range(df, 5)
        m_high, m_low = get_range(df, 21)

        m3_high, m3_low = get_range(df, 63)
        m6_high, m6_low = get_range(df, 126)
        m9_high, m9_low = get_range(df, 189)
        m12_high, m12_low = get_range(df, 252)

        return {
            "symbol": symbol,
            "chart_symbol": chart_symbol,
            "price": price,
            "signal": signal,
            "confidence": confidence,

            "d_high": d_high,
            "d_low": d_low,

            "w_high": w_high,
            "w_low": w_low,

            "m_high": m_high,
            "m_low": m_low,

            "m3_high": m3_high,
            "m3_low": m3_low,

            "m6_high": m6_high,
            "m6_low": m6_low,

            "m9_high": m9_high,
            "m9_low": m9_low,

            "m12_high": m12_high,
            "m12_low": m12_low,
        }

    except Exception as e:
        print("ERROR:", e)
        return None

@app.route("/")
def home():
    scored = []

    for s in STOCKS:
        data = get_stock(s["symbol"], s["chart_symbol"])
        if data:
            scored.append(data)

    if not scored:
        return "No market data available."

    best = max(scored, key=lambda x: x["confidence"])

    selected = request.args.get("symbol")
    if selected:
        for s in scored:
            if s["symbol"] == selected:
                best = s

    return render_template(
        "index.html",
        scored=scored,
        best=best,
        now=datetime.now()
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
